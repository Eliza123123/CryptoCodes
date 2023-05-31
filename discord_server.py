from discord_webhook import DiscordWebhook


def send_to_acme_channel(discord_message):
    content = ""
    for item in discord_message:
        if isinstance(item, list):
            content += ' '.join([str(i) for i in item]) + '\n'
        else:
            content += item + '\n'
    webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1113461647399'
                                 '452732/F7NZ2hduBuF1GjUYzI1PjPkjMs_BzrtoUNTp2yq'
                                 'Ksr4WP6lWe7EJH-x1-p9HrQegRt4I'
                             , content=content)
    response = webhook.execute()
