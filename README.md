[comment]: # "Auto-generated SOAR connector documentation"
# discord_kczernik5

Publisher: discord  
Connector Version: 1.0.0  
Product Vendor: Discord_clone_1723108489099_clone_1723121852701_clone_1723198218502_clone_1723463646231  
Product Name: Discord_clone_1723108489099_clone_1723121852701_clone_1723198218502_clone_1723463646231  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2.134  

Integrate with Discord to post messages and attachments to channels

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Discord_clone_1723108489099_clone_1723121852701_clone_1723198218502_clone_1723463646231 asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  required  | string | Discord bot token
**guild_id** |  optional  | numeric | server/guild id

### Supported Actions  
[test connectivity](#action-test-connectivity) - Tests authorization with Discord  
[list guilds](#action-list-guilds) - List guilds of a Discord bot is a member of  
[list channels](#action-list-channels) - List Channels of a specific guild  
[get message](#action-get-message) - gets information about the message, such as: attachments, embeds, content, author and creation date timestamp  

## action: 'test connectivity'
Tests authorization with Discord

Type: **test**  
Read only: **True**

Checks that the provided bot token is valid.

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'list guilds'
List guilds of a Discord bot is a member of

Type: **investigate**  
Read only: **True**

The output of this action is a list of all guilds (servers) a Discord bot is a member of. The guilds will be listed with their corresponding guild IDs.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |  
action_result.data.\*.\*.id | string |  `discord guild id`  |  
action_result.data.\*.\*.name | string |  `discord guild name`  |  
action_result.data.\*.\*.icon | string |  `icon`  |  
action_result.data.\*.\*.owner | boolean |  |   True  False 
action_result.data.\*.\*.baner | string |  `baner`  |  
action_result.data.\*.\*.permissions | string |  `permissions`  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'list channels'
List Channels of a specific guild

Type: **investigate**  
Read only: **True**

The output of this action is a list of all channels of a specific guild. The channels will be listed with their corresponding channel IDs.

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**guild_id** |  required  | guilds id | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.guild_id | string |  |  
action_result.data.\*.\*.id | string |  `discord channel id`  |  
action_result.data.\*.\*.name | string |  `discord channel name`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'get message'
gets information about the message, such as: attachments, embeds, content, author and creation date timestamp

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**channel_id** |  required  | channel id | string | 
**message_id** |  required  | message id | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.message origin.channel id | numeric |  `channel id`  |  
action_result.data.\*.message origin.channel name | string |  `channel name`  |  
action_result.data.\*.message data.message id | numeric |  `message id`  |  
action_result.data.\*.message data.date | numeric |  `message date`  |  
action_result.data.\*.author data.author id | numeric |  `author id`  |  
action_result.data.\*.author data.author name | string |  `author name`  |  
action_result.data.\*.attachments | string |  `attachments`  |  
action_result.data.\*.embeds | string |  `embeds`  |  
action_result.data.\*.content | string |  `message content`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |  