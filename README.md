[comment]: # "Auto-generated SOAR connector documentation"
# Discord

Publisher: discord  
Connector Version: 1.0.0  
Product Vendor: Discord  
Product Name: Discord  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2.134  

Integrate with Discord to post messages and attachments to channels

# Splunk> Phantom

Welcome to the open-source repository for Splunk> Phantom's discord App.

Please have a look at our [Contributing Guide](https://github.com/Splunk-SOAR-Apps/.github/blob/main/.github/CONTRIBUTING.md) if you are interested in contributing, raising issues, or learning more about open-source Phantom apps.

## Legal and License

This Phantom App is licensed under the Apache 2.0 license. Please see our [Contributing Guide](https://github.com/Splunk-SOAR-Apps/.github/blob/main/.github/CONTRIBUTING.md#legal-notice) for further details.


### Configuration Variables

The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a Discord asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  required  | password | Discord bot token

### Supported Actions  
[test connectivity](#action-test-connectivity) - Tests authorization with Discord  
[list guilds](#action-list-guilds) - List guilds of a Discord bot is a member of  
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