import json
import sys

interpreter = sys.executable.split("/")[-1]

with open("./sessions.txt", "r") as f:
    sessions = [i.strip() for i in f.readlines()]


def split_list(lst, chunk_size=50):
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


each_50 = split_list(sessions)

apps = []

for x, y in enumerate(each_50, 1):
    sessions_file = f"sessions_{x}.txt"

    with open(sessions_file, "w") as f:
        f.write("\n".join(y))

    apps.append(
        {
            "name": f"gifts{x}",
            "script": "main.py",
            "interpreter": interpreter,
            "log_date_format": "YYYY-MM-DD HH:mm:ss",
            "env": {"SESSIONS_PATH": sessions_file},
            "autorestart": True,
            "watch": False,
        }
    )

apps.append(
    {
        "name": "server",
        "script": "server.py",
        "interpreter": interpreter,
        "log_date_format": "YYYY-MM-DD HH:mm:ss",
        "autorestart": True,
        "watch": False,
    }
)


with open("ecosystem.config.js", "w+") as f:
    f.write("module.exports = " + json.dumps({"apps": apps}, indent=2) + ";")


print("Now you can run the following command: pm2 start ecosystem.config.js")
