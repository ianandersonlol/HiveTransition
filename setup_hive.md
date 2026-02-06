Go to https://hippo.ucdavis.edu/ sign in with your kerberos account and select "HIVE" to create a HIVE account. 

hive_setup_1.png


Then fill out the form as follows. I will include a tutorial for setting up an ssh key below if you don't have one.

hive_setup_2.png



Windows (PowerShell)
Check if an SSH Key Exists:

Open PowerShell and run:

Test-Path "$HOME\.ssh\id_rsa.pub"
If it returns True, you already have an SSH key.
If it returns False, you need to create one.
Create an SSH Key (if needed):

In PowerShell, run:

ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
Press Enter to accept the default file location.
Optionally, enter a passphrase for added security.
Copy the Public Key to Clipboard:

Run the following command to copy your public key:

Get-Content "$HOME\.ssh\id_rsa.pub" | Set-Clipboard
Your public key is now copied and ready to be pasted into HIVE’s SSH key text box.
macOS and Linux Terminal
Check if an SSH Key Exists:

Open your Terminal and run:

if [ -f ~/.ssh/id_rsa.pub ]; then echo "SSH key exists"; else echo "No SSH key found"; fi
If the message confirms an existing key, you’re set.
If not, proceed to create one.
Create an SSH Key (if needed):

Run the following command:

ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
Press Enter to confirm the default location.
Optionally, add a passphrase for additional security.
Copy the Public Key:

On macOS:

pbcopy < ~/.ssh/id_rsa.pub
This copies your public key to the clipboard.

On Linux:

If you have xclip installed:
xclip -selection clipboard < ~/.ssh/id_rsa.pub
Alternatively, you can display the key in the terminal and manually copy it:
cat ~/.ssh/id_rsa.pub
For Windows Users Using WSL
PowerShell vs. WSL Terminal:
In PowerShell: Follow the Windows instructions above to manage your native Windows SSH keys.
In WSL Terminal: Repeat the macOS/Linux instructions within your WSL environment since WSL maintains its own file system and SSH configuration.


Thanks, and happy computing! 