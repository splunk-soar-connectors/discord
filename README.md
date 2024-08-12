[comment]: # "Auto-generated SOAR connector documentation"
# Discord

Publisher: discord  
Connector Version: 1.0.0  
Product Vendor: Discord  
Product Name: Discord  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2.134  

Integrate with Discord to post messages and attachments to channels

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Discord asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  required  | password | Discord bot token
**guild_id** |  required  | numeric | Guild ID

### Supported Actions  
[test connectivity](#action-test-connectivity) - Tests authorization with Discord  
[list channels](#action-list-channels) - List Channels of a specific guild  

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
List Channels of a specific guild

Type: **investigate**  
Read only: **True**

The output of this action is a list of all channels of a specific guild. The channels will be listed with their corresponding channel IDs.

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.guild_id | string |  |  
action_result.data.\*.id | string |  `channel id`  |  
action_result.data.\*.name | string |  `channel name`  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |  