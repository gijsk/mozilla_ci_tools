"""
This script retriggers N times every job that matches --includes and doesn't match --exclude .

usage:
python th_filters.py repo rev --includes "args to include" --exclude  "args to exclude --times N"
"""
import logging
import urllib

from argparse import ArgumentParser

from mozci.mozci import trigger_range, query_repo_name_from_buildername, query_builders

logging.basicConfig(format='%(asctime)s %(levelname)s:\t %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S')
LOG = logging.getLogger()


def parse_args(argv=None):
    """Parse command line options."""
    parser = ArgumentParser()

    # Required arguments

    parser.add_argument("repo",
                        help='Branch name')

    parser.add_argument("rev",
                        help='The 12 character representing a revision (most recent).')

    parser.add_argument('-i', "--includes",
                        dest="includes",
                        required=True,
                        type=str,
                        help="Treeherder filters to include.")

    parser.add_argument('-e', "--exclude",
                        dest="exclude",
                        type=str,
                        help="Treeherder filters to exclude.")

    parser.add_argument("--times",
                        dest="times",
                        type=int,
                        default=1,
                        help="Number of times to retrigger the push.")

    parser.add_argument("--limit",
                        dest="lim",
                        type=int,
                        default=100,
                        help="Maximum number of buildernames to trigger.")

    parser.add_argument("--dry-run",
                        action="store_true",
                        dest="dry_run",
                        help="flag to test without actual push.")

    parser.add_argument("--debug",
                        action="store_true",
                        dest="debug",
                        help="set debug for logging.")

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

    filters_in = options.includes.split(' ') + [options.repo]
    buildernames = query_builders()

    for word in filters_in:
        buildernames = filter(lambda x: word in x, buildernames)

    if options.exclude:
        filters_out = options.exclude.split(' ')

        for word in filters_out:
            buildernames = filter(lambda x: word not in x, buildernames)

    if len(buildernames) > options.lim:
        LOG.info('There %i matching buildernames, the limit is %i. If you really want'
                 'to trigger everything, try again with --limit %i.' % (len(buildernames),
                                                                        options.lim, options.lim))
        exit(1)

    for buildername in buildernames:
        trigger_range(
            buildername=buildername,
            revisions=[options.rev],
            times=options.times,
            dry_run=options.dry_run,
        )

        LOG.info('https://treeherder.mozilla.org/#/jobs?%s' %
                 urllib.urlencode({'repo': query_repo_name_from_buildername(buildername),
                                   'fromchange': options.rev,
                                   'tochange': options.rev,
                                   'filter-searchStr': buildername}))


if __name__ == '__main__':
    main()
