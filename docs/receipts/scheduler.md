## Periodic Task Scheduler

Periodic task scheduler is a contrib module in `starlette_web`. 
It operates with system-wide task scheduler, so it has no outer dependencies to track list of tasks.

- For POSIX systems, Crontab is used (based on `django-crontab`)
- For Windows, Task Scheduler 2.0 is used (based on `win_tasks.py` from `salt`)

For both runners, maximum frequency of running jobs is **1 per minute**.

## Plugging-in

- Add `starlette_web.contrib.scheduler` to settings.INSTALLED_APPS
- Configure list of periodic jobs and other settings (see below)
- (Optionally) configure logger `starlette_web.contrib.scheduler`

## Usage

```bash
python command.py scheduler add
python command.py scheduler remove
python command.py scheduler show
python command.py scheduler run d41d8cd98f00b204e9800998ecf8427e  # run by OS-scheduler
```

## Settings

- `PERIODIC_JOBS_LIST` - list of periodic jobs entries. Each entry is a list with 5 elements:
  - crontab-like schedule pattern (including "@reboot")
  - import string for **asynchronous** task handler
  - args
  - kwargs
  - timeout (optional)  

  Format:  
    `JobType = Tuple[str, str, List[JSONType], Dict[str, JSONType], Union[float, None]]`
    
  Example:
  - ```python
    PERIODIC_JOBS_LIST = [
        [  
            "* * * * *", 
            "starlette_web.common.management.base.call_command", 
            ["test_command", ["--arg1=value1"]], 
            {}, 
            5.0,
        ],
    ]
    ```

- `PERIODIC_JOBS_LOCK` (bool) - prevent starting a job if an old instance of the same job is still running,
  by default **True**
- `PERIODIC_JOBS_PYTHON_EXECUTABLE` (str) - link to Python executable, by default `sys.executable`
- `PERIODIC_JOBS_RUN_DIRECTORY` (str) - entrypoint for job runner, by default `os.getcwd() / PROJECT_ROOT_DIR`
- `PERIODIC_JOBS_COMMAND_PREFIX` (str, POSIX only) - prefix for job command, 
  by default `"cd %PERIODIC_JOBS_RUN_DIRECTORY% && "`
- `PERIODIC_JOBS_COMMAND_SUFFIX` (str, POSIX only) - suffix for job command, by default empty string
- `PERIODIC_JOBS_CRONTAB_EXECUTABLE` (str, POSIX only) - by default `"/usr/bin/crontab"`
- `PERIODIC_JOBS_CRONTAB_LINE_PATTERN` (str, POSIX only) - by default `"%(time)s %(command)s # %(comment)s"`
- `PERIODIC_JOBS_USERNAME` (str, Windows only) - by default `"System"`
- `PERIODIC_JOBS_PASSWORD` (str, Windows only) - by default `None`
