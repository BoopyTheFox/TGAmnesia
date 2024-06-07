import asyncio
import argparse
import os
from crontab import CronTab

# Initialize the cron for the current user
try:
    cron = CronTab(user=True)
except TypeError:
    cron = CronTab()


def human_to_cron(time_interval):
    special_expressions = {
        '@hourly': '@hourly',
        '@daily': '@daily',
        '@weekly': '@weekly',
        '@monthly': '@monthly',
        '@yearly': '@yearly',
        '@annually': '@annually'
    }
    
    if time_interval in special_expressions:
        return special_expressions[time_interval]
    
    time_value = int(time_interval[:-1])
    time_unit = time_interval[-1]

    if time_unit == 'm':
        return f"*/{time_value} * * * *"
    elif time_unit == 'h':
        return f"0 */{time_value} * * *"
    elif time_unit == 'd':
        return f"0 0 */{time_value} * *"
    else:
        raise ValueError("Invalid time interval format. Use 'm' for minutes, 'h' for hours, 'd' for days, or special expressions like '@hourly'.")


def cron_to_human(cron_expression):
    special_expressions = {
        '* * * * *': 'every minute',
        '@hourly': 'every hour',
        '@daily': 'every day',
        '@weekly': 'every week',
        '@monthly': 'every month',
        '@yearly': 'every year',
        '@annually': 'every year'
    }
    
    if cron_expression in special_expressions:
        return special_expressions[cron_expression]
    
    fields = cron_expression.split()
    if len(fields) != 5:
        raise ValueError("Invalid cron expression. Must have 5 fields.")

    minute, hour, day_of_month, month, day_of_week = fields

    def get_frequency(field, name, singular):
        if field == "*":
            return ""
        elif field.startswith("*/"):
            return f"every {field[2:]} {name}"
        else:
            return f"at {field} {singular if field == '1' else name}s"

    parts = [
        get_frequency(minute, "minute", "minute"),
        get_frequency(hour, "hour", "hour"),
        get_frequency(day_of_month, "day of the month", "day"),
        get_frequency(month, "month", "month"),
        get_frequency(day_of_week, "day of the week", "day")
    ]

    # Filter out empty parts and join the remaining parts with commas
    human_readable = ', '.join(part for part in parts if part)
    
    return human_readable if human_readable else "Invalid cron expression"


async def schedule_purge(group_name, time_interval):
    # Get the current working directory
    path = os.getcwd()

    # Check if the job already exists
    for job in cron:
        if f'#TGAmnesia_{group_name}' in job.comment:
            msg = f"Job for group '{group_name}' already exists."
            print(msg)
            return msg

    ## bash -l -c '' ## - this way, cron in docker will preserve ENV variables (path to python)
    ## if [ -d "venv" ]; then . venv/bin/activate; fi ## - for non-docker usage
    command = f'bash -l -c \'cd {path} && if [ -d "venv" ]; then . venv/bin/activate; fi && python TGAmnesia_core.py --group-purge {group_name}\''

    job = cron.new(command=command, comment=f'#TGAmnesia_{group_name}')
    
    try:
        cron_expr = human_to_cron(time_interval)
    except ValueError as e:
        msg = str(e)
        print(msg)
        return msg

    job.setall(cron_expr)
    cron.write()
    human_readable = cron_to_human(cron_expr)
    msg = f"Scheduled job for group '{group_name}' {human_readable}."
    print(msg)
    return msg


async def list_jobs():
    messages = []
    for job in cron:
        if '#TGAmnesia' in job.comment:
            job_name = job.comment.split('_')[1]
            if job.is_valid():
                msg_line = f"Job for group '{job_name}': {cron_to_human(job.slices.render())}"
            else:
                msg_line = f"Job for group '{job_name}' is not valid."
            print(msg_line)
            messages.append(msg_line)
    
    msg = "\n".join(messages)
    if not msg:
        msg = "No purge jobs scheduled."
    return msg


async def remove_job(group_name):
    removed_any = False
    if group_name.lower() == 'all':
        for job in cron:
            if '#TGAmnesia' in job.comment:
                cron.remove(job)
                removed_any = True
        if removed_any:
            cron.write()
            msg = "Removed all jobs."
        else:
            msg = "No jobs found to remove."
    else:
        for job in cron:
            if f'#TGAmnesia_{group_name}' in job.comment:
                cron.remove(job)
                cron.write()
                msg = f"Removed job for group '{group_name}'."
                print(msg)
                return msg
        msg = f"No job found for group '{group_name}'."

    print(msg)
    return msg


def main():
    parser = argparse.ArgumentParser(description="TGAmnesia Scheduler")
    parser.add_argument('--schedule-purge', nargs=2, metavar=('group_name', 'time_interval'), help='Schedule a purge for a group')
    parser.add_argument('--list-jobs', action='store_true', help='List all scheduled jobs')
    parser.add_argument('--rm-job', type=str, help='Remove a scheduled job by group name')

    args = parser.parse_args()

    if args.schedule_purge:
        group_name, time_interval = args.schedule_purge
        asyncio.run(schedule_purge(group_name, time_interval))
    elif args.list_jobs:
        asyncio.run(list_jobs())
    elif args.rm_job:
        asyncio.run(remove_job(args.rm_job))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

