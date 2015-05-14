#! /usr/bin/env python

from argparse import ArgumentParser
import logging

from mozci.mozci import trigger_job
from mozci.platforms import build_talos_buildernames_for_repo

logging.basicConfig(format='%(asctime)s %(levelname)s:\t %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S')
LOG = logging.getLogger()

PGO_ONLY_BRANCHES = ['mozilla-aurora', 'mozilla-beta']


def parse_args(argv=None):
    '''
    Parse command line options.
    '''
    parser = ArgumentParser()

    parser.add_argument("--repo-name",
                        dest="repo_name",
                        required=True,
                        help="The name of the repository: e.g. 'cedar'.")

    parser.add_argument("--times",
                        dest="times",
                        required=True,
                        type=int,
                        help="Number of times to retrigger the push.")

    parser.add_argument("--rev",
                        dest="revision",
                        help="revision of the push.")

    parser.add_argument("--dry-run",
                        action="store_true",
                        dest="dry_run",
                        help="flag to test without actual push.")

    parser.add_argument("--debug",
                        action="store_true",
                        dest="debug",
                        help="set debug for logging.")

    parser.add_argument("--pgo",
                        action="store_true",
                        dest="pgo",
                        help="trigger pgo tests (not non-pgo).")

    parser.add_argument("--filter",
                        action="store",
                        dest="filterstring",
                        help="comma-separated substring filter indicating which jobs to retrigger")

    parser.add_argument("--platform",
                        action="store",
                        default="all",
                        choices=["desktop", "android", "all"],
                        help="indicate which platform to run jobs for (default: all)")

    options = parser.parse_args(argv)
    return options


def main():
    options = parse_args()

    if options.debug:
        LOG.setLevel(logging.DEBUG)
        logging.getLogger("requests").setLevel(logging.DEBUG)
        LOG.info("Setting DEBUG level")
    else:
        LOG.setLevel(logging.INFO)
        # requests is too noisy and adds no value
        logging.getLogger("requests").setLevel(logging.WARNING)

    pgo = False
    if options.repo_name in PGO_ONLY_BRANCHES or options.pgo:
        pgo = True

    buildernames = build_talos_buildernames_for_repo(options.repo_name, pgo)

    jobfilters = None
    if options.filterstring:
        jobfilters = options.filterstring.split(',')

    for buildername in buildernames:
        try:
            buildername.index("ndroid")
            # This is an android build; if we only want desktop, ignore:
            if options.platform == "desktop":
                continue
        except:
            # This is a desktop build; if we only want android, ignore:
            if options.platform == "android":
                continue

        if jobfilters:
            shouldrun = False
            for jobfilter in jobfilters:
                try:
                    buildername.index(jobfilter)
                    shouldrun = True
                    break
                except:
                    pass

            if not shouldrun:
                LOG.info("Not triggering " + buildername + " due to filter.")
                continue

        trigger_job(revision=options.revision,
                    buildername=buildername,
                    times=options.times,
                    dry_run=options.dry_run)

if __name__ == '__main__':
    main()
