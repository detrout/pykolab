<?php
    \$rcmail_config['kolab_folders_configuration_default'] = 'Configuration';
    \$rcmail_config['kolab_folders_event_default'] = 'Calendar';
    \$rcmail_config['kolab_folders_contact_default'] = 'Contacts';
    \$rcmail_config['kolab_folders_task_default'] = '';
    \$rcmail_config['kolab_folders_note_default'] = '';
    \$rcmail_config['kolab_folders_journal_default'] = '';
    \$rcmail_config['kolab_folders_mail_inbox'] = 'INBOX';
    \$rcmail_config['kolab_folders_mail_drafts'] = 'Drafts';
    \$rcmail_config['kolab_folders_mail_sentitems'] = 'Sent';
    \$rcmail_config['kolab_folders_mail_junkemail'] = 'Spam';
    \$rcmail_config['kolab_folders_mail_outbox'] = '';
    \$rcmail_config['kolab_folders_mail_wastebasket'] = 'Trash';

    if (file_exists(RCMAIL_CONFIG_DIR . '/' . \$_SERVER["HTTP_HOST"] . '/' . basename(__FILE__))) {
        include_once(RCMAIL_CONFIG_DIR . '/' . \$_SERVER["HTTP_HOST"] . '/' . basename(__FILE__));
    }

?>
