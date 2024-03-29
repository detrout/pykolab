# standard standalone server implementation

START {
    # do not delete this entry!
    recover	cmd="ctl_cyrusdb -r"

    # this is only necessary if using idled for IMAP IDLE
    idled		cmd="idled"
}

# UNIX sockets start with a slash and are put into /var/lib/imap/sockets
SERVICES {
    # add or remove based on preferences
    imap		cmd="imapd" listen="imap" prefork=5
    imaps		cmd="imapd -s" listen="imaps" prefork=1
    pop3		cmd="pop3d" listen="pop3" prefork=3
    pop3s		cmd="pop3d -s" listen="pop3s" prefork=1
    sieve		cmd="timsieved" listen="sieve" prefork=0

    ptloader    cmd="ptloader" listen="/var/lib/imap/ptclient/ptsock" prefork=0

    # these are only necessary if receiving/exporting usenet via NNTP
    #nntp		cmd="nntpd" listen="nntp" prefork=3
    #nntps		cmd="nntpd -s" listen="nntps" prefork=1

    # at least one LMTP is required for delivery
    #lmtp		cmd="lmtpd" listen="lmtp" prefork=0
    lmtpunix	cmd="lmtpd" listen="/var/lib/imap/socket/lmtp" prefork=1

    # this is only necessary if using notifications
    notify	cmd="notifyd" listen="/var/lib/imap/socket/notify" proto="udp" prefork=1
}

EVENTS {
    # this is required
    checkpoint	cmd="ctl_cyrusdb -c" period=30

    # this is only necessary if using duplicate delivery suppression,
    # Sieve or NNTP
    duplicate_prune cmd="cyr_expire -E 3" at=0400

    # Expire data older then 69 days. Two full months of 31 days
    # each includes two full backup cycles, plus 1 week margin
    # because we run our full backups on the first sat/sun night
    # of each month.
    delete_prune cmd="cyr_expire -E 4 -D 69" at=0430
    expunge_prune cmd="cyr_expire -E 4 -X 69" at=0445

    # this is only necessary if caching TLS sessions
    tlsprune	cmd="tls_prune" at=0400

    # Create search indexes regularly
    squatter    cmd="squatter -s -i" at=0530
}
