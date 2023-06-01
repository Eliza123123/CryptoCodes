import requests

URL = 'https://discord.com/api/webhooks/1113680454193774653/3f_xCJOG_0ehKHl4neTWyrNXoRd4yj-3sCo7JSqeqU2UwCwF0czwuY_RmHPINlUTGSGY'

def send_to_acme_channel(zs_table, table, confirmation):

    content = ("\n" + "-" * 65 + "\n").join([zs_table, table])

    result = requests.post(URL, json={
        "content": f"```{content}\n\n{confirmation}```",
        "username": "ACME"
    })

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
