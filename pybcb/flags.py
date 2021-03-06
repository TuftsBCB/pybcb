import argparse
import multiprocessing as mp
import os
import os.path
import sys
import tempfile

__parser = argparse.ArgumentParser(
    description='bcb experiment framework',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
add = __parser.add_argument
config = None

def use_all(*names):
    for name in names:
        use(name)


__used_flags = []
def use(name, fun=None):
    if fun is not None:
        add, verify = fun
    else:
        assert name in __flags, 'Could not find %s in flags' % name
        add, verify = __flags[name]

    add()
    __used_flags.append((name, verify))


def used(name):
    return hasattr(config, name.replace('-', '_'))


def assert_flags(*names):
    for name in names:
        assert_flag(name)


def assert_flag(name):
    if not used(name):
        eprintln('Flag %s is required by this experiment.' % name)
        sys.exit(1)


def init():
    global config

    if not any(map(lambda (name, _): name == 'verbose', __used_flags)):
        use('verbose')

    config = __parser.parse_args()
    def getopt(name):
        return getattr(config, name.replace('-', '_'))

    for name, verify in __used_flags:
        if verify is not None:
            err = verify(getopt(name))
            if err != True:
                eprintln('Error setting flag %s: %s' % (name, err))
                sys.exit(1)
        if config.verbose:
            eprintln('Flag %s set to "%s".' % (name, getopt(name)))


def verify_hhsuite():
    if not os.getenv('HHLIB'):
        return 'HHLIB environment variable is not set.'

    hhlib = os.getenv('HHLIB')
    if not os.access(hhlib, os.R_OK):
        return 'HHLIB is not accessible: %s' % hhlib
    return True


# Assumes verify_hhsuite has already run.
def verify_hhsuite_db(prefix):
    fp = os.path.join(os.getenv('HHLIB'), 'data', prefix)
    # There are more files in a HHblits database, but check the two
    # most important ones.
    return verify_path('%s_hhm_db' % fp) and verify_path('%s_a3m_db' % fp)


# Assumes verify_hhsuite has already run.
def verify_pdb_hhm_db(prefix):
    fp = os.path.join(os.getenv('HHLIB'), 'data', prefix)
    return verify_path(fp)


def verify_path(fp):
    if not os.access(fp, os.R_OK):
        return 'Cannot read %s' % fp
    return True


def make_path(fp):
    if os.access(fp, os.R_OK):
        return True
    try:
        os.makedirs(fp)
    except Exception, e:
        return 'Cannot makedirs for %s because %s' % (fp, e)
    return verify_path(fp)


def eprintln(s):
    print >> sys.stderr, s


def aa(*args, **kwargs):
    return lambda: add(*args, **kwargs)
__flags = {
    'pdb-dir': (
        aa('--pdb-dir', dest='pdb_dir', type=str,
           default='/data/bio/pdb',
           help='The location of a full PDB directory.'),
        verify_path,
    ),
    'sabmark-dir': (
        aa('--sabmark-dir', dest='sabmark_dir', type=str,
           default='/data/bio/SABmark',
           help='The location of the SABmark directory with PDB files, '+
                'and "sup_fp" and "twi_fp" sub-directories.'),
        verify_path,
    ),
    'sabmark-set': (
        aa('--sabmark-set', dest='sabmark_set', type=str,
           choices=['twilight', 'superfamily'],
           default='superfamily',
           help='The SABmark alignment set to use.'),
        None,
    ),
    'frag-lib': (
        aa('--frag-lib', dest='frag_lib', type=str,
           default=os.path.join(
                     os.getenv('FRAGLIB_PATH', '/data/bio/fraglibs'),
                     'structure/400-11.json',
                   ),
           help='Path to a structure fragment library.'),
        None,
    ),
    'bow-db': (
        aa('--bow-db', dest='bow_db', type=str,
           default='/data/bio/bowdbs/pdb',
           help='The location of a BOW database.'),
        verify_path,
    ),
    'pdb-hhm-db': (
        aa('--pdb-hhm-db', dest='pdb_hhm_db', type=str,
           default='pdb-select25-2012',
           help='The location of a PDB-HHM database generated '+
                'by `build-pdb-hhm-db`. As with seq_hhm_db, this should '+
                'be the prefix of the database. The full path is derived '+
                'from the HHLIB environment variable.'),
        lambda v: verify_hhsuite() and verify_pdb_hhm_db(v),
    ),
    'seq-hhm-db': (
        aa('--seq-hhm-db', dest='seq_hhm_db', type=str,
           default='nr20',
           help='The location of an HHblits database downloaded from '+
                'the HHsuite database. Note that this is ONLY the prefix'+
                'of the database. The full path is derived from the '+
                'HHLIB environment variable.'+
                'Typical values: nr20 or uniprot20.'),
        lambda v: verify_hhsuite() and verify_hhsuite_db(v),
    ),
    'hhfrag-inc': (
        aa('--hhfrag-inc', dest='hhfrag_inc', type=int,
           default=5,
           help='The window increment step to use with HHfrag.'),
        None,
    ),
    'hhfrag-min': (
        aa('--hhfrag-min', dest='hhfrag_min', type=int,
           default=30,
           help='The minimum window size to use with HHfrag.'),
        None,
    ),
    'hhfrag-max': (
        aa('--hhfrag-max', dest='hhfrag_max', type=int,
           default=35,
           help='The maximum window size to use with HHfrag.'),
        None,
    ),
    'blits': (
        aa('--noblits', dest='blits', action='store_false',
           help='When set, HHsearch will be used in lieu of HHblits.'),
        None,
    ),
    'results-dir': (
        aa('--results-dir', dest='results_dir', type=str,
           default=os.path.join('.', 'experiments', 'results',
                                os.path.basename(sys.argv[0])),
           help='The directory where results are stored.'),
        make_path,
    ),
    'cpu': (
        aa('--cpu', dest='cpu', type=int, default=mp.cpu_count(),
           help='The maximum number of CPUs executing simultaneously.'),
        None,
    ),
    'no-cache': (
        aa('--no-cache', dest='no_cache', type=str, nargs='+',
           default=[], metavar='EXT',
           help='A list of extensions for which to force regeneration. '+
                'That is, if a file generated by a command already exists '+
                'and has an extension in this list, then the file will be '+
                'overwritten instead of reused.'),
        None,
    ),
    'ignore-cache': (
        aa('--ignore-cache', dest='ignore_cache', action='store_true',
           help='When set, the cache is never used.'),
        None,
    ),
    'tmp-dir': (
        aa('--tmp-dir', dest='tmp_dir', type=str,
           default=os.path.join(tempfile.gettempdir(), 'pybcb',
                                os.path.basename(sys.argv[0])),
           help='A scratch directory to store transient data for this '+
                'experiment.'),
        make_path,
    ),
    'verbose': (
        aa('--quiet', dest='verbose', action='store_false',
           help='Emit as much diagnostic output as possible.'),
        None,
    ),
}

