import argparse
import datetime
import json
import logging
import time

from .common import Context, connect, find_history, print_json

log = logging.getLogger('abm')


def do_list(context: Context, args: list):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--state', help='list jobs in this state', required=False)
    parser.add_argument(
        '--history', help='show jobs in the given history', required=False
    )
    parser.add_argument('-u', '--user', help='show jobs for this user', required=False)
    argv = parser.parse_args(args)

    log.debug('Connecting to the Galaxy server')
    gi = connect(context)

    if argv.state:
        log.debug(f"Getting jobs with state {argv.state}")
    else:
        log.debug("Getting full job list")
    if argv.history:
        history_id = find_history(gi, argv.history)
        if history_id is None:
            print("ERROR: No such history")
            return
    job_list = gi.jobs.get_jobs(
        state=argv.state, history_id=argv.history, user_id=argv.user
    )
    log.debug(f"Iterating over job list with {len(job_list)} items")
    for job in job_list:
        print(f"{job['id']}\t{job['state']}\t{job['update_time']}\t{job['tool_id']}")


def show(context: Context, args: list):
    if len(args) != 1:
        print("ERROR: Invalid parameters. Job ID is required")
        return
    gi = connect(context)
    job = gi.jobs.show_job(args[0], full_details=True)
    print(json.dumps(job, indent=4))


def wait(context: Context, args: list):
    parser = argparse.ArgumentParser()
    parser.add_argument('job_id')
    parser.add_argument('-t', '--timeout', default=-1)
    params = parser.parse_args(args)
    timeout = params.timeout
    job_id = params.job_id
    gi = connect(context)
    start_time = time.time()  # we only interested in precision to the second
    waiting = True
    while waiting:
        job = gi.jobs.show_job(job_id, full_details=False)
        if job is None or len(job) == 0:
            print(f"Job {job_id} not found.")
            return
        state = job["state"]
        if timeout > 0:
            if time.time() - start_time > timeout:
                waiting = False
        if state == "ok" or state == "error":
            waiting = False
        if waiting:
            time.sleep(15)
    print(json.dumps(job, indent=4))


def get_value(metric: dict):
    if metric['name'] == 'runtime_seconds':
        return metric['raw_value']
    return metric['value']


def metrics(context: Context, args: list):
    if len(args) == 0:
        print("ERROR: no job ID provided")
        return
    gi = connect(context)
    if len(args) > 1:
        arg = args.pop(0)
        if arg in ['-h', '--history']:
            history_id = args.pop(0)
            log.debug(f"Getting metrics for jobs from history {history_id}")
            job_list = gi.jobs.get_jobs(history_id=history_id)
            metrics = []
            for job in job_list:
                metrics.append(
                    {
                        'job_id': job['id'],
                        'job_state': job['state'],
                        'tool_id': job['tool_id'],
                        'job_metrics': gi.jobs.get_metrics(job['id']),
                    }
                )
        else:
            print(f"ERROR: Unrecognized argument {arg}")
    else:
        job = gi.jobs.show_job(args[0])
        metrics = [
            {
                'job_id': job['id'],
                'job_state': job['state'],
                'tool_id': job['tool_id'],
                'job_metrics': gi.jobs.get_metrics(args[0]),
            }
        ]
    print(json.dumps(metrics, indent=4))
    # metrics = {}
    # for m in gi.jobs.get_metrics(args[0]):
    #     metrics[m['name']] = get_value(m)
    # try:
    #     print(f"{metrics['galaxy_slots']},{metrics['galaxy_memory_mb']},{metrics['runtime_seconds']}")
    # except:
    #     print(',,')


def cancel(context: Context, args: list):
    if len(args) == 0:
        print('ERROR: no job ID provided.')
        return
    gi = connect(context)
    state = ''
    history = None
    jobs = []
    while len(args) > 0:
        arg = args.pop(0)
        if arg in ['-s', '--state']:
            state = args.pop(0)
        elif arg in ['-h', '--history']:
            history = find_history(gi, args.pop(0))
            if history is None:
                print("ERROR: No such history")
                return
        else:
            jobs.append(arg)
    if state or history:
        if len(jobs) > 0:
            print(
                "ERROR: To many parameters. Either filter by state or history, or list job IDs"
            )
            return
        jobs = [job['id'] for job in gi.jobs.get_jobs(state=state, history_id=history)]
    for job in jobs:
        if gi.jobs.cancel_job(job):
            print(f"Job {job} canceled")
        else:
            print(
                f"ERROR: Unable to cancel {job}, job was already in a terminal state."
            )


def problems(context: Context, args: list):
    if len(args) == 0:
        print('ERROR: no job ID provided.')
        return
    gi = connect(context)
    print_json(gi.jobs.get_common_problems(args[0]))


def rerun(context: Context, args: list):
    remap = False
    if '-r' in args:
        remap = True
        args.remove('-r')
    if '--remap' in args:
        remap = True
        args.remove('--remap')
    if len(args) == 0:
        print("ERROR: no job ID provided")
        return
    gi = connect(context)
    result = gi.jobs.rerun_job(args[0], remap=remap)
    print_json(result)
