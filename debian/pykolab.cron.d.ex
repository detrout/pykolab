#
# Regular cron jobs for the pykolab package
#
0 4	* * *	root	[ -x /usr/bin/pykolab_maintenance ] && /usr/bin/pykolab_maintenance
