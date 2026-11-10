# Management account provisioning

Create a new management account only from an administrator-controlled terminal:

```powershell
.\venv\Scripts\python.exe manage.py create_management_account <username>
```

The command prompts for a password and confirmation without echoing either value. It validates the password with the configured Django password validators, rejects an existing username, and stores the account using Django's password-hashing manager. It does not create a reusable default password, set Django's `is_staff` flag, or print the password.

Do not pass passwords as command-line arguments, environment variables, fixtures, or application responses. For an existing account whose password may have been disclosed, use Django's interactive `changepassword` command from an administrator-controlled terminal and notify the account owner through the normal secure channel. This provisioning command does not change or remove existing accounts.
