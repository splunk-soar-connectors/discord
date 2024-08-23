[comment]: # "Auto-generated SOAR connector documentation"
# Discord

Publisher: Splunk  
Connector Version: 1.0.0  
Product Vendor: Discord  
Product Name: Discord  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2.134  

Integrate with Discord to post messages and analyze attachments sent to channels

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Discord asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  required  | string | Discord bot token
**guild_id** |  required  | numeric | Guild aka server ID

Where to find bot token: https://support-dev.discord.com/hc/en-us/articles/6470840524311-Why-can-t-I-copy-my-bot-s-token

What is guild: https://support.discord.com/hc/en-us/articles/23187611406999-Guilds-FAQ

Where to find guild ID: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID#h_01HRSTXPS5FSFA0VWMY2CKGZXA


### Supported Actions  
[test connectivity](#action-test-connectivity) - Tests authorization with Discord  
[list channels](#action-list-channels) - List text channels of a guild  
[send message](#action-send-message) - Send a message to the Discord channel  
[kick user](#action-kick-user) - Kicks user from a guild  
[ban user](#action-ban-user) - Bans user from a guild  
[fetch message](#action-fetch-message) - gets information about the message, such as: attachments, embeds, content, author, creation and edition date, it also shows jump url to the fetched message  
[delete message](#action-delete-message) - removes the message  
[get user](#action-get-user) - Get information about a user of a Discord guild/server  

## action: 'test connectivity'
Tests authorization with Discord

Type: **test**  
Read only: **True**

Checks that the provided bot token is valid.

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'list channels'
List text channels of a guild

Type: **investigate**  
Read only: **True**

The output of this action is a list of all text channels for the guild. The channels will be listed with their corresponding channel IDs.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.guild_id | string |  `discord guild id`  |  
action_result.data.\*.id | string |  `discord channel id`  |  
action_result.data.\*.name | string |  `discord channel name`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'send message'
Send a message to the Discord channel

Type: **generic**  
Read only: **False**

Send a message to Discord

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**destination** |  required  | Discord channels ID | string |  `discord channel id` 
**message** |  required  | Message to send | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.destination | string |  `discord channel id`  |  
action_result.parameter.message | string |  |  
action_result.data.\*.message_id | string |  `discord message id`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'kick user'
Kicks user from a guild

Type: **correct**  
Read only: **False**

Kicks user from a guild

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**user_id** |  required  | User ID | string |  `discord user id` 
**reason** |  optional  | The reason the user got kicked. | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.user_id | string |  `discord user id`  |  
action_result.parameter.reason | string |  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'ban user'
Bans user from a guild

Type: **correct**  
Read only: **False**

Bans user from a guild and deletes specific number of seconds worth of messages

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**user_id** |  required  | User ID | string |  `discord user id` 
**delete_message_seconds** |  optional  | The number of seconds worth of messages to delete from the user in the guild. The minimum is 0 and the maximum is 604800 (7 days). Defaults to 1 day. | numeric | 
**reason** |  optional  | The reason the user got kicked. | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.user_id | string |  `discord user id`  |  
action_result.parameter.delete_message_seconds | numeric |  |  
action_result.parameter.reason | string |  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'fetch message'
gets information about the message, such as: attachments, embeds, content, author, creation and edition date, it also shows jump url to the fetched message

Type: **investigate**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**channel_id** |  required  | channel id | string |  `discord channel id` 
**message_id** |  required  | message id | string |  `discord message id` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.message origin.channel id | numeric |  `discord channel id`  |  
action_result.data.\*.message origin.channel name | string |  `discord channel name`  |  
action_result.data.\*.message data.created at | numeric |  `date`  |  
action_result.data.\*.message data.edited at | numeric |  `date`  |  
action_result.data.\*.author data.author id | numeric |  `author id`  |  
action_result.data.\*.author data.author name | string |  `author name`  |  
action_result.data.\*.attachments | string |  `artifact id`  |  
action_result.data.\*.embeds | string |  `artifact id`  |  
action_result.data.\*.content | string |  `message content`  |  
action_result.data.\*.jump url | string |  `url`  |  
action_result.data.\*.flags | string |  `flags`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'delete message'
removes the message

Type: **correct**  
Read only: **False**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**channel_id** |  required  | channel id | string |  `discord channel id` 
**message_id** |  required  | message id | string |  `discord message id` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.channel_id | numeric |  `discord channel id`  |  
action_result.parameter.message_id | numeric |  `discord message id`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'get user'
Get information about a user of a Discord guild/server

Type: **investigate**  
Read only: **True**

This action will get information about a user.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**user_id** |  required  | user id | string |  `discord user id` 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.user_id | string |  `discord user id`  |  
action_result.data.\*.display_name | string |  |  
action_result.data.\*.name | string |  |  
action_result.data.\*.created_at | string |  |  
action_result.data.\*.system | string |  |  
action_result.data.\*.public_flags | string |  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |  