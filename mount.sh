echo "$SSHPASS" | sshfs "$RSYNCNETUSERHOST": /mnt -o StrictHostKeyChecking=no -o password_stdin
