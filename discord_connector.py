# File: discord_connector.py
#
# Copyright (c) 2024 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.

import asyncio
import dataclasses
import json

# Phantom App imports
import phantom.app as phantom
import requests
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector

import discord
from discord_artifact import Artifact
from discord_consts import *


class RetVal(tuple):

    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class DiscordConnector(BaseConnector):

    def __init__(self):
        super().__init__()

        self._state = None
        self._base_url = "https://discord.com/api/v10"
        self._session = None
        self._guild = None
        self._client = None
        self._token = None
        self._guild_id = None
        self._loop = None

    def _get_error_message_from_exception(self, e):
        """ This method is used to get appropriate error message from the exception.
        :param e: Exception object
        :return: error message
        """
        error_code = None
        error_message = "Error message unnavigable"

        self.error_print("Error occurred.", e)

        try:
            if hasattr(e, "args"):
                if len(e.args) > 1:
                    error_code = e.args[0]
                    error_message = e.args[1]
                elif len(e.args) == 1:
                    error_message = e.args[0]
        except Exception as e:
            self.error_print("Error occurred while fetching exception information. Details: {}".format(str(e)))

        if not error_code:
            error_text = "Error Message: {}".format(error_message)
        else:
            error_text = "Error Code: {}. Error Message: {}".format(error_code, error_message)

        return error_text

    def _handle_test_connectivity(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))

        try:
            self._loop.run_until_complete(self._client.login(self._token))
            if self._client.status != discord.Status.online:
                self.save_progress("Test Connectivity Failed.")
        except Exception as e:
            err = self._get_error_message_from_exception(e)
            return action_result.set_status(phantom.APP_ERROR, err)

        self.save_progress("Test Connectivity Passed")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_fetch_message(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id = param['channel_id']
        message_id = param['message_id']

        status, message = self.fetch_message(channel_id, message_id, action_result)
        if not status:
            return action_result.set_status(phantom.APP_ERROR,
                                            "action result: fetching message {} ended with failure".format(message_id))

        attachments, embeds = self.create_artifacts(message)
        message = self.parse_message(message, attachments, embeds)

        action_result.add_data(message)
        summary = action_result.update_summary({})
        summary['action result: '] = "fetching message {} ended with success".format(message_id)

        return action_result.set_status(phantom.APP_SUCCESS)

    def fetch_message(self, channel_id, message_id, action_result) -> discord.Message or None:
        status, channel = self.run_in_loop(self._guild.fetch_channel(channel_id), action_result,
                                           error_message=DISCORD_ERROR_FETCHING_CHANNEL)
        if not status:
            return status, None
        status, message = self.run_in_loop(channel.fetch_message(message_id), action_result,
                                           error_message=DISCORD_ERROR_FETCHING_MESSAGE)

        return status, message

    def create_artifacts(self, message):
        container_id = self.get_container_id()
        attachments = []
        embeds = []

        if message.embeds:
            self.save_progress("working on embeds")
            for embed in message.embeds:
                embeds.append(self.create_embed_artifact(embed, container_id))

        if message.attachments:
            self.save_progress("working on attachments")
            for attachment in message.attachments:
                attachments.append(self.create_attachment_artifact(attachment, container_id))

        return attachments, embeds

    def create_embed_artifact(self, embed, container_id):
        artifact = Artifact(
            container_id=container_id,
            name=f"embed: {embed.title}",
            cef={"URL": embed.url, "Description": embed.description}
        )
        return self.save_artifact_to_soar(dataclasses.asdict(artifact))

    def create_attachment_artifact(self, attachment, container_id):
        artifact = Artifact(
            container_id=container_id,
            name=f"attachment: {attachment.filename}",
            cef={"URL": attachment.url, "Description": attachment.description, "Type": attachment.content_type}
        )
        return self.save_artifact_to_soar(dataclasses.asdict(artifact))

    def save_artifact_to_soar(self, artifact):
        status, creation_message, artifact_id = self.save_artifact(artifact)
        self.save_progress("creating artifact: status: {}, creation message: {}, artifact id {}"
                           .format(status, creation_message, artifact_id))
        return artifact_id

    def parse_message(self, message, attachments, embeds):
        return {
            "message origin": {
                "channel id": message.channel.id,
                "channel name": message.channel.name,
            },
            "message data": {
                "created at": str(message.created_at),
                "edited at": str(message.edited_at) if message.edited_at is not None else "message was not edited",
            },
            "author data": {
                "author id": message.author.id,
                "author name": message.author.name,
            },
            "jump url": message.jump_url,
            "flags": [flag[:1] for flag in list(filter((lambda flag: flag[1]), message.flags))] or "no flags",
            "attachments": attachments or "no attachments",
            "embeds": embeds or "no embeds",
            "content": message.content
        }

    def _handle_delete_message(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id = param['channel_id']
        message_id = param['message_id']

        status = self.delete_message(channel_id, message_id, action_result)

        summary = action_result.update_summary({})
        summary['action result: '] = "Deleting message {} ended with {}".format(message_id,
                                                                                "success" if status else "failure")
        return action_result.set_status(phantom.APP_SUCCESS) if status else action_result.set_status(phantom.APP_ERROR)

    def delete_message(self, channel_id, message_id, action_result):
        status, message = self.fetch_message(channel_id, message_id, action_result)
        if not status:
            return status
        status, result = self.run_in_loop(message.delete(), action_result, error_message=DISCORD_ERROR_DELETING_MESSAGE)
        return status

    async def _load_guild(self):
        await self._client.login(self._token)
        self._guild = await self._client.fetch_guild(self._guild_id)

    def _handle_list_channels(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        status, channels = self.run_in_loop(self._guild.fetch_channels(), action_result,
                                            error_message=DISCORD_ERROR_FETCHING_CHANNEL)

        for channel in channels:
            if channel.type == discord.ChannelType.text:
                action_result.add_data({
                    "name": channel.name,
                    "id": channel.id
                })

        summary = action_result.update_summary({})
        summary['num_channels'] = len([channel for channel in channels if channel.type == discord.ChannelType.text])

        return status

    def _handle_send_message(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        destination = param['destination']
        message = param['message']

        status, channel = self.run_in_loop(self._guild.fetch_channel(destination), action_result,
                                           error_message=DISCORD_ERROR_FETCHING_CHANNEL)
        status, message = self.run_in_loop(channel.send(message), action_result,
                                           error_message=DISCORD_ERROR_SENDING_MESSAGE)

        action_result.add_data({
            "message_id": message.id
        })

        return status

    def _handle_kick_user(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id = param['user_id']
        reason = param.get('reason', "")

        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result,
                                        error_message=DISCORD_ERROR_FETCHING_MEMBER)
        status, result = self.run_in_loop(self._guild.kick(user, reason=reason), action_result,
                                          error_message=DISCORD_ERROR_KICKING_MEMBER)

        return status

    def _handle_ban_user(self, param):

        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id = param['user_id']
        reason = param.get('reason', "")
        delete_message_seconds = param.get('delete_message_seconds', 86400)

        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result,
                                        error_message=DISCORD_ERROR_FETCHING_MEMBER)
        status, result = self.run_in_loop(
            self._guild.ban(user, reason=reason, delete_message_seconds=delete_message_seconds), action_result,
            error_message=DISCORD_ERROR_BANING_MEMBER)

        return status

    def _handle_get_user(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id = param['user_id']

        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result,
                                        error_message=DISCORD_ERROR_FETCHING_MEMBER)

        action_result.add_data({
            "display_name": user.display_name,
            "name": user.name,
            "created_at": str(user.created_at),
            "system": user.system,
            "public_flags": user.public_flags.all()
        })

        return status

    def run_in_loop(self, coroutine, action_result, error_message=""):
        try:
            return action_result.set_status(phantom.APP_SUCCESS), self._loop.run_until_complete(coroutine)
        except discord.DiscordException as e:
            err = self._get_error_message_from_exception(e)
            self.save_progress(f"Exception found type: {e.__class__.__name__}")
            return action_result.set_status(phantom.APP_ERROR,
                                            f"{error_message} Error type: {e.__class__.__name__} Details: {err}"), None
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR,
                                            f"Other exception. Error type: {e.__class__.__name__} Details: {str(e)}"), None

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'fetch_message':
            ret_val = self._handle_fetch_message(param)
        if action_id == 'delete_message':
            ret_val = self._handle_delete_message(param)
        if action_id == 'list_channels':
            ret_val = self._handle_list_channels(param)
        if action_id == 'send_message':
            ret_val = self._handle_send_message(param)
        if action_id == 'kick_user':
            ret_val = self._handle_kick_user(param)
        if action_id == 'ban_user':
            ret_val = self._handle_ban_user(param)
        if action_id == 'get_user':
            ret_val = self._handle_get_user(param)
        if action_id == 'test_connectivity':
            ret_val = self._handle_test_connectivity(param)

        return ret_val

    def initialize(self):
        # Load the state in initialize, use it to store data
        self._state = self.load_state()
        # get the asset config
        config = self.get_config()

        self._base_url = "https://discord.com/api/v10"
        self._token = config['token']
        self._guild_id = config['guild_id']

        intents = discord.Intents.all()
        self._client = discord.Client(intents=intents)

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._load_guild())
        except discord.DiscordException as e:
            self.save_progress(f"Exception found type: {e.__class__.__name__}")
            return phantom.APP_ERROR
        except Exception:
            return phantom.APP_ERROR

        return phantom.APP_SUCCESS

    def finalize(self):
        # Save the state, this data is saved across actions and app upgrades
        self._client.close()
        self._loop.close()
        self.save_state(self._state)
        return phantom.APP_SUCCESS


def main():
    import argparse

    argparser = argparse.ArgumentParser()

    argparser.add_argument('input_test_json', help='Input Test JSON file')
    argparser.add_argument('-u', '--username', help='username', required=False)
    argparser.add_argument('-p', '--password', help='password', required=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password

    if username is not None and password is None:
        # User specified a username but not a password, so ask
        import getpass
        password = getpass.getpass("Password: ")

    if username and password:
        try:
            login_url = DiscordConnector._get_phantom_base_url() + '/login'

            print("Accessing the Login page")
            r = requests.get(login_url, verify=False)
            csrftoken = r.cookies['csrftoken']

            data = dict()
            data['username'] = username
            data['password'] = password
            data['csrfmiddlewaretoken'] = csrftoken

            headers = dict()
            headers['Cookie'] = 'csrftoken=' + csrftoken
            headers['Referer'] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=False, data=data, headers=headers)
            session_id = r2.cookies['sessionid']
        except Exception as e:
            print("Unable to get session id from the platform. Error: " + str(e))
            exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = DiscordConnector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json['user_session_token'] = session_id
            connector._set_csrf_info(csrftoken, headers['Referer'])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    exit(0)


if __name__ == '__main__':
    main()
