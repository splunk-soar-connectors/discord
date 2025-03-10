# File: discord_connector.py
#
# Copyright (c) 2025 Splunk Inc.
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
from collections.abc import Sequence
from datetime import datetime
from typing import List, Optional, Union

# Phantom App imports
import phantom.app as phantom
import pytz
import requests
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector

import discord
from discord.abc import GuildChannel
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
        """This method is used to get appropriate error message from the exception.
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
            self.error_print(f"Error occurred while fetching exception information. Details: {str(e)}")

        if not error_code:
            error_text = f"Error Message: {error_message}"
        else:
            error_text = f"Error Code: {error_code}. Error Message: {error_message}"

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
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id: int = param["channel_id"]
        message_id: int = param["message_id"]

        status, message = self.fetch_message(channel_id, message_id, action_result)
        if not status:
            return action_result.set_status(phantom.APP_ERROR, f"action result: fetching message {message_id} ended with failure")

        attachments, embeds = self.create_artifacts(message)
        message = self.parse_message(message, attachments, embeds)

        action_result.add_data(message)
        summary = action_result.update_summary({})
        summary["action result: "] = f"fetching message {message_id} ended with success"

        return action_result.set_status(phantom.APP_SUCCESS)

    def fetch_message(self, channel_id: int, message_id: int, action_result: ActionResult) -> tuple[bool, Optional[discord.Message]]:
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
        message: discord.Message

        status, channel = self.run_in_loop(self._guild.fetch_channel(channel_id), action_result, error_message=DISCORD_ERROR_FETCHING_CHANNEL)
        if not status:
            return status, None
        status, message = self.run_in_loop(channel.fetch_message(message_id), action_result, error_message=DISCORD_ERROR_FETCHING_MESSAGE)

        return status, message

    def create_artifacts(self, message: discord.Message) -> tuple[list[Optional[int]], list[Optional[int]]]:
        container_id: str = self.get_container_id()
        attachments = []
        embeds = []

        if message.embeds:
            self.save_progress("working on embeds")
            embed: discord.Embed
            for embed in message.embeds:
                embeds.append(self.create_embed_artifact(embed, container_id))

        if message.attachments:
            self.save_progress("working on attachments")
            attachment: discord.Attachment
            for attachment in message.attachments:
                attachments.append(self.create_attachment_artifact(attachment, container_id))

        return attachments, embeds

    def create_embed_artifact(self, embed: discord.Embed, container_id: str):
        artifact = Artifact(container_id=container_id, name=f"embed: {embed.title}", cef={"URL": embed.url, "Description": embed.description})
        return self.save_artifact_to_soar(artifact)

    def create_attachment_artifact(self, attachment: discord.Attachment, container_id: str):
        artifact = Artifact(
            container_id=container_id,
            name=f"attachment: {attachment.filename}",
            cef={"URL": attachment.url, "Description": attachment.description, "Type": attachment.content_type},
        )
        return self.save_artifact_to_soar(artifact)

    def save_artifact_to_soar(self, artifact: Artifact) -> Optional[int]:
        status, creation_message, artifact_id = self.save_artifact(dataclasses.asdict(artifact))
        self.save_progress(f"creating artifact: status: {status}, creation message: {creation_message}, artifact id {artifact_id}")
        return artifact_id

    def parse_message(self, message: discord.Message, attachments: List[Optional[int]], embeds: List[Optional[int]]):
        return {
            "message_origin": {
                "channel_id": str(message.channel.id),
                "channel_name": str(message.channel.name),
            },
            "message data": {
                "created_at": str(message.created_at),
                "edited_at": str(message.edited_at) if message.edited_at is not None else "message was not edited",
            },
            "author_data": {
                "author_id": str(message.author.id),
                "author_name": str(message.author.name),
            },
            "jump_url": message.jump_url,
            "flags": [flag[0] for flag in filter(lambda flag: flag[1], message.flags)] or "no flags",
            "attachments": attachments or "no attachments",
            "embeds": embeds or "no embeds",
            "content": message.content,
        }

    def _handle_delete_message(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id: int = param["channel_id"]
        message_id: int = param["message_id"]

        status = self.delete_message(channel_id, message_id, action_result)

        summary = action_result.update_summary({})
        result = "success" if status else "failure"
        summary["action result: "] = f"Deleting message {message_id} ended with {result}"
        return action_result.set_status(phantom.APP_SUCCESS) if status else action_result.set_status(phantom.APP_ERROR)

    def delete_message(self, channel_id: int, message_id: int, action_result: ActionResult):
        status, message = self.fetch_message(channel_id, message_id, action_result)
        if not status:
            return status
        status, _ = self.run_in_loop(message.delete(), action_result, error_message=DISCORD_ERROR_DELETING_MESSAGE)
        return status

    async def _load_guild(self):
        await self._client.login(self._token)
        self._guild = await self._client.fetch_guild(self._guild_id)

    def _handle_list_channels(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        channels: Sequence[GuildChannel]
        status, channels = self.run_in_loop(self._guild.fetch_channels(), action_result, error_message=DISCORD_ERROR_FETCHING_CHANNEL)

        for channel in channels:
            if channel.type == discord.ChannelType.text:
                action_result.add_data({"name": channel.name, "id": str(channel.id)})

        summary = action_result.update_summary({})
        summary["num_channels"] = len([channel for channel in channels if channel.type == discord.ChannelType.text])

        return status

    def _handle_send_message(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        destination: int = param["destination"]
        message_to_send: str = param["message"]

        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
        status, channel = self.run_in_loop(self._guild.fetch_channel(destination), action_result, error_message=DISCORD_ERROR_FETCHING_CHANNEL)

        message: discord.Message
        status, message = self.run_in_loop(channel.send(message_to_send), action_result, error_message=DISCORD_ERROR_SENDING_MESSAGE)

        action_result.add_data({"message_id": str(message.id)})

        return status

    def _handle_kick_user(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id: int = param["user_id"]
        reason: str = param.get("reason", "")

        user: discord.Member
        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result, error_message=DISCORD_ERROR_FETCHING_MEMBER)
        status, _ = self.run_in_loop(self._guild.kick(user, reason=reason), action_result, error_message=DISCORD_ERROR_KICKING_MEMBER)
        return status

    def _handle_ban_user(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id: int = param["user_id"]
        reason: str = param.get("reason", "")
        delete_message_seconds = param.get("delete_message_seconds", 86400)

        user: discord.Member
        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result, error_message=DISCORD_ERROR_FETCHING_MEMBER)
        status, _ = self.run_in_loop(
            self._guild.ban(user, reason=reason, delete_message_seconds=delete_message_seconds),
            action_result,
            error_message=DISCORD_ERROR_BANING_MEMBER,
        )

        return status

    def _handle_fetch_message_history(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id: int = param["channel_id"]

        status_after, fetching_start_date = self.parse_date(param.get("fetching_start_date", None))
        status_before, fetching_end_date = self.parse_date(param.get("fetching_end_date", None))

        limit: Optional[int] = param.get("limit", None)
        if limit == 0:
            limit = None

        if limit < 0:
            return action_result.set_status(phantom.APP_ERROR, "action result: limit must be greater than or equal to 0.")

        oldest_first: bool = param.get("oldest_first", False)

        self.save_progress(f"status_after {status_after}: {fetching_start_date} | status_before {status_before}: {fetching_end_date}")
        if not (status_after and status_before):
            return action_result.set_status(
                phantom.APP_ERROR, f"action result: fetching messages from {channel_id} " f"channel ended with failure, unable to format date"
            )

        messages: list[discord.Message]
        status, messages = self.fetch_message_history(channel_id, action_result, fetching_start_date, fetching_end_date, oldest_first, limit)
        if not status:
            return action_result.set_status(phantom.APP_ERROR, f"action result: fetching messages from {channel_id} channel ended with failure")

        for message in messages:
            action_result.add_data(
                {
                    "message id": str(message.id),
                    "author id": str(message.author.id),
                    "created at": str(message.created_at),
                    "embeds_attachments": True if (message.attachments or message.embeds) else False,
                    "content": message.content,
                }
            )

        summary = action_result.update_summary({})
        summary["action result: "] = f"action result: fetching messages from {channel_id} channel ended with success"
        return action_result.set_status(phantom.APP_SUCCESS)

    def parse_date(self, date_string: str) -> tuple[bool, Optional[datetime]]:
        if date_string is None:
            return True, None
        try:
            date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return True, date.replace(tzinfo=pytz.UTC)
        except ValueError:
            return False, None

    def fetch_message_history(
        self,
        channel_id: int,
        action_result: ActionResult,
        fetching_start_date: Optional[datetime],
        fetching_end_date: Optional[datetime],
        oldest_first,
        limit: Optional[int],
    ) -> tuple[bool, Optional[list[discord.Message]]]:

        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
        status, channel = self.run_in_loop(self._guild.fetch_channel(channel_id), action_result, "Cannot fetch channel from Discord.")
        if not status:
            return status, None

        messages: list[discord.Message]
        status, messages = self.run_in_loop(
            self.gather_messages(channel, fetching_start_date, fetching_end_date, oldest_first, limit),
            action_result,
            "Cannot fetch messages from Discord.",
        )

        return status, messages

    async def gather_messages(
        self,
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel],
        fetching_start_date: Optional[datetime],
        fetching_end_date: Optional[datetime],
        oldest_first: bool,
        limit: Optional[int],
    ) -> list[discord.Message]:

        messages = [
            message
            async for message in channel.history(limit=limit, after=fetching_start_date, before=fetching_end_date, oldest_first=oldest_first)
        ]

        self.save_progress(
            f"gathered messages: {len(messages)} while working with parameters: after: {fetching_start_date} | before: {fetching_end_date}"
        )
        return messages

    def _handle_get_user(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        user_id: int = param["user_id"]
        user: discord.Member
        status, user = self.run_in_loop(self._guild.fetch_member(user_id), action_result, error_message=DISCORD_ERROR_FETCHING_MEMBER)

        action_result.add_data(
            {
                "display_name": user.display_name,
                "name": user.name,
                "created_at": str(user.created_at),
                "system": user.system,
                "public_flags": user.public_flags.all(),
            }
        )

        return status

    def run_in_loop(self, coroutine, action_result: ActionResult, error_message: str = "") -> tuple[bool, Optional[any]]:
        try:
            return action_result.set_status(phantom.APP_SUCCESS), self._loop.run_until_complete(coroutine)
        except discord.DiscordException as e:
            err = self._get_error_message_from_exception(e)
            self.save_progress(f"Exception found type: {e.__class__.__name__}")
            return action_result.set_status(phantom.APP_ERROR, f"{error_message} Error type: {e.__class__.__name__} Details: {err}"), None
        except Exception as e:
            return action_result.set_status(phantom.APP_ERROR, f"Other exception. Error type: {e.__class__.__name__} Details: {str(e)}"), None

    def _handle_on_poll(self, param):
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        container_count = param.get("container_count", None)

        status, channels = self.run_in_loop(self._guild.fetch_channels(), action_result, error_message=DISCORD_ERROR_FETCHING_CHANNEL)
        if not status:
            self.save_progress("action result: Cannot Poll messages, unable to fetch channels ")
            return action_result.set_status(phantom.APP_ERROR, DISCORD_ERROR_FETCHING_MESSAGE)

        self._status = self.load_state()
        last_poll_date = self._state.get("last_poll_date", None)
        if last_poll_date is not None:
            validation_pass, last_poll_date = self.parse_date(last_poll_date)
            if not validation_pass:
                return action_result.set_status(phantom.APP_ERROR, "Unable to parse last poll date")

        self.save_progress(f"lading last poll date: {last_poll_date}")

        newest_message: datetime = last_poll_date or datetime.min.replace(tzinfo=pytz.UTC)

        for channel in filter(
            (lambda channel_to_test: isinstance(channel_to_test, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel))), channels
        ):

            status, messages = self.fetch_message_history(channel.id, action_result, last_poll_date, None, True, container_count)
            if not status:
                self.debug_print(f"action result: Cannot Poll messages from {channel.name} {channel.id}")
                return action_result.set_status(phantom.APP_ERROR)

            self.save_progress("saving the containers")
            for message in messages:

                _, message_creation_date = self.parse_date(message.created_at.strftime("%Y-%m-%d %H:%M:%S"))
                newest_message = max(message_creation_date, newest_message)

                if message_creation_date != last_poll_date:
                    ret_val = self.save_on_poll_container(message, channel)
                    if phantom.is_fail(ret_val):
                        return action_result.set_status(phantom.APP_ERROR, f"Unable to create container: {message}")

        newest_message = newest_message.replace(tzinfo=pytz.UTC)
        self.save_progress(f"saving last poll date: {str(newest_message)[:-6]}")
        self._state["last_poll_date"] = str(newest_message)[:-6]
        self.save_state(self._state)

        action_result = self.add_action_result(ActionResult(dict(param)))
        return action_result.set_status(phantom.APP_SUCCESS)

    def save_on_poll_container(self, message: discord.Message, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]):

        contains_embeds_or_attachments = True if (message.attachments or message.embeds) else False

        container = {
            "name": f"message {message.id} on channel {channel.name}",
            "description": "generated by on poll action",
            "sensitivity": "White" if not contains_embeds_or_attachments else "Green",
        }

        ret_val, ret_message, container_id = self.save_container(container)

        self.save_progress(f"container saved finished: return value: {ret_val} | message: {ret_message} | container_id: {container_id}")

        artifact = Artifact(
            container_id=str(container_id),
            name=str(message.id),
            cef={
                "contains embeds or attachments": contains_embeds_or_attachments,
                "message creation date": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "content": message.content,
            },
        )
        self.save_artifact(dataclasses.asdict(artifact))

        return ret_val

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == "fetch_message":
            ret_val = self._handle_fetch_message(param)
        if action_id == "delete_message":
            ret_val = self._handle_delete_message(param)
        if action_id == "list_channels":
            ret_val = self._handle_list_channels(param)
        if action_id == "send_message":
            ret_val = self._handle_send_message(param)
        if action_id == "kick_user":
            ret_val = self._handle_kick_user(param)
        if action_id == "ban_user":
            ret_val = self._handle_ban_user(param)
        if action_id == "fetch_message_history":
            ret_val = self._handle_fetch_message_history(param)
        if action_id == "on_poll":
            ret_val = self._handle_on_poll(param)
        if action_id == "get_user":
            ret_val = self._handle_get_user(param)
        if action_id == "test_connectivity":
            ret_val = self._handle_test_connectivity(param)

        return ret_val

    def initialize(self):
        # Load the state in initialize, use it to store data

        self._state = self.load_state()
        if not isinstance(self._state, dict):
            self.debug_print("State file format is not valid")
            self._state = {}
            self.save_state(self._state)
            self.debug_print("Recreated the state file with current app_version")
            self._state = self.load_state()
            if self._state is None:
                self.debug_print("Please check the owner, owner group, and the permissions of the state file")
                self.debug_print(
                    "The Splunk SOAR user should have correct access rights and ownership for the \
                    corresponding state file"
                )
                return phantom.APP_ERROR

        # get the asset config
        config = self.get_config()

        self._base_url = "https://discord.com/api/v10"
        self._token = config["token"]
        self._guild_id = config["guild_id"]

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
        self._loop.run_until_complete(self.end_connection())
        self._loop.close()
        if self._state is not None:
            self.save_state(self._state)
        return phantom.APP_SUCCESS

    async def end_connection(self):
        await self._client.close()


def main():
    import argparse

    argparser = argparse.ArgumentParser()

    argparser.add_argument("input_test_json", help="Input Test JSON file")
    argparser.add_argument("-u", "--username", help="username", required=False)
    argparser.add_argument("-p", "--password", help="password", required=False)

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
            login_url = DiscordConnector._get_phantom_base_url() + "/login"

            print("Accessing the Login page")
            r = requests.get(login_url, verify=False)
            csrftoken = r.cookies["csrftoken"]

            data = dict()
            data["username"] = username
            data["password"] = password
            data["csrfmiddlewaretoken"] = csrftoken

            headers = dict()
            headers["Cookie"] = "csrftoken=" + csrftoken
            headers["Referer"] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=False, data=data, headers=headers)
            session_id = r2.cookies["sessionid"]
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
            in_json["user_session_token"] = session_id
            connector._set_csrf_info(csrftoken, headers["Referer"])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    exit(0)


if __name__ == "__main__":
    main()
