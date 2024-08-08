[comment]: # "Auto-generated SOAR connector documentation"
# discord2

Publisher: discord  
Connector Version: 1.0.0  
Product Vendor: discord  
Product Name: discord  
Product Version Supported (regex): ".\*"  
Minimum Product Version: 6.2.2.134  

discord

# Splunk> Phantom

Welcome to the open-source repository for Splunk> Phantom's discord App.

Please have a look at our [Contributing Guide](https://github.com/Splunk-SOAR-Apps/.github/blob/main/.github/CONTRIBUTING.md) if you are interested in contributing, raising issues, or learning more about open-source Phantom apps.

## Legal and License

This Phantom App is licensed under the Apache 2.0 license. Please see our [Contributing Guide](https://github.com/Splunk-SOAR-Apps/.github/blob/main/.github/CONTRIBUTING.md#legal-notice) for further details.


### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a discord asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  required  | password | discord bot token

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[list gulds](#action-list-gulds) - ;list guild (channels)  
[list channels](#action-list-channels) - list channels of specific guild  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'list gulds'
;list guild (channels)

Type: **contain**  
Read only: **False**

#### Action Parameters
No parameters are required for this action

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |    

## action: 'list channels'
list channels of specific guild

Type: **contain**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**guild_id** |  required  | guilds id | string | 

#### Action Output
DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.guild_id | string |  |  
action_result.status | string |  |  
action_result.message | string |  |  
summary.total_objects | numeric |  |  
summary.total_objects_successful | numeric |  |  