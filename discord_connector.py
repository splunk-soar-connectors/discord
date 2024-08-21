#!/usr/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------
# Phantom sample App Connector python file
# -----------------------------------------
# from lib2to3.fixes.fix_input import context

# Phantom App imports
import phantom.app as phantom
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector

from discord_consts import *
import requests
import json
import discord
import asyncio
from bs4 import BeautifulSoup

from discord_artifact import Artifact, artifact_to_dict


class RetVal(tuple):

    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class DiscordConnector(BaseConnector):

    def __init__(self):

        # Call the BaseConnectors init first
        super(DiscordConnector, self).__init__()

        self._state = None
        self._base_url = "https://discord.com/api/v10"

        self._async_loop = None
        self._client = None
        self._guild_id = None
        self._guild = None
        self._token = None
        self._headers = None

    def _process_empty_response(self, response, action_result):
        if response.status_code == 200:
            return RetVal(phantom.APP_SUCCESS, {})

        return RetVal(
            action_result.set_status(
                phantom.APP_ERROR, "Empty response and no information in the header"
            ), None
        )

    def _process_html_response(self, response, action_result):
        # An html response, treat it like an error
        status_code = response.status_code

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            error_text = soup.text
            split_lines = error_text.split('\n')
            split_lines = [x.strip() for x in split_lines if x.strip()]
            error_text = '\n'.join(split_lines)
        except:
            error_text = "Cannot parse error details"

        message = "Status Code: {0}. Data from server:\n{1}\n".format(status_code, error_text)

        message = message.replace(u'{', '{{').replace(u'}', '}}')
        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_json_response(self, r, action_result):
        # Try a json parse
        try:
            resp_json = r.json()
        except Exception as e:
            return RetVal(
                action_result.set_status(
                    phantom.APP_ERROR, "Unable to parse JSON response. Error: {0}".format(str(e))
                ), None
            )

        # Please specify the status codes here
        if 200 <= r.status_code < 399:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        # You should process the error returned in the json
        message = "Error from server. Status Code: {0} Data from server: {1}".format(
            r.status_code,
            r.text.replace(u'{', '{{').replace(u'}', '}}')
        )

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_response(self, r, action_result):
        # store the r_text in debug data, it will get dumped in the logs if the action fails
        if hasattr(action_result, 'add_debug_data'):
            action_result.add_debug_data({'r_status_code': r.status_code})
            action_result.add_debug_data({'r_text': r.text})
            action_result.add_debug_data({'r_headers': r.headers})

        # Process each 'Content-Type' of response separately

        # Process a json response
        if 'json' in r.headers.get('Content-Type', ''):
            return self._process_json_response(r, action_result)

        # Process an HTML response, Do this no matter what the api talks.
        # There is a high chance of a PROXY in between phantom and the rest of
        # world, in case of errors, PROXY's return HTML, this function parses
        # the error and adds it to the action_result.
        if 'html' in r.headers.get('Content-Type', ''):
            return self._process_html_response(r, action_result)

        # it's not content-type that is to be parsed, handle an empty response
        if not r.text:
            return self._process_empty_response(r, action_result)

        # everything else is actually an error at this point
        message = "Can't process response from server. Status Code: {0} Data from server: {1}".format(
            r.status_code,
            r.text.replace('{', '{{').replace('}', '}}')
        )

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _make_rest_call(self, endpoint, action_result, method="get", **kwargs):
        # **kwargs can be any additional parameters that requests.request accepts

        config = self.get_config()

        resp_json = None

        try:
            request_func = getattr(requests, method)
        except AttributeError:
            return RetVal(
                action_result.set_status(phantom.APP_ERROR, "Invalid method: {0}".format(method)),
                resp_json
            )

        # Create a URL to connect to
        url = self._base_url + endpoint

        try:
            r = request_func(
                url,
                # auth=(username, password),  # basic authentication
                verify=config.get('verify_server_cert', False),
                **kwargs
            )
        except Exception as e:
            return RetVal(
                action_result.set_status(
                    phantom.APP_ERROR, "Error Connecting to server. Details: {0}".format(str(e))
                ), resp_json
            )

        return self._process_response(r, action_result)

    def _handle_test_connectivity(self, param):
        # Add an action result object to self (BaseConnector) to represent the action for this param
        action_result = self.add_action_result(ActionResult(dict(param)))

        self.save_progress("Connecting to endpoint")
        # make rest call
        headers = {"Authorization": "Bot " + self._token}

        ret_val, response = self._make_rest_call(
            '/gateway/bot', action_result, params=None, headers=headers
        )

        if phantom.is_fail(ret_val):
            self.save_progress("Test Connectivity Failed.")
            return action_result.get_status()

        self.save_progress("Test Connectivity Passed")
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_guilds(self, param):
        self.debug_print("param", param)
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        ret_val, response = self._make_rest_call(
            '/users/@me/guilds', action_result, params=None, headers=self._headers
        )

        if phantom.is_fail(ret_val):
            self.save_progress("List Guilds Failed.")
            return action_result.get_status()

        action_result.add_data(response)
        summary = action_result.update_summary({})
        summary['num_guilds'] = len(response)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_channels(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        guild_id = param['guild_id']

        ret_val, response = self._make_rest_call(
            '/guilds/' + guild_id + '/channels', action_result, params=None, headers=self._headers
        )

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        action_result.add_data(response)
        summary = action_result.update_summary({})
        summary['num_channels'] = len(response)
        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_fetch_message(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))

        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id = param['channel_id']
        message_id = param['message_id']

        message = self._async_loop.run_until_complete(self.fetch_message(channel_id, message_id))
        if message is None:
            return action_result.set_status(phantom.APP_ERROR, "Failed to fetch message")

        attachments, embeds = self.create_artifacts(message)
        message = self.parse_message(message, attachments, embeds)

        action_result.add_data(message)
        summary = action_result.update_summary({})
        summary['success: '] = "fetching message completed"

        return action_result.set_status(phantom.APP_SUCCESS)

    async def fetch_message(self, channel_id, message_id):

        try:
            channel = await self._guild.fetch_channel(channel_id)
            self.save_progress("channel: {}".format(str(channel)))
            message = await channel.fetch_message(message_id)
            self.save_progress("message: {}".format(str(message)))

        except discord.HTTPException as e:
            self.save_progress("Failed to fetch message: {}".format(str(e)))
            return None

        return message

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
        return self.save_artifact_to_soar(artifact_to_dict(artifact))

    def create_attachment_artifact(self, attachment, container_id):
        artifact = Artifact(
            container_id=container_id,
            name=f"embed: {attachment.title}",
            cef={"URL": attachment.url, "Description": attachment.description, "Type": attachment.content_type}
        )
        return self.save_artifact_to_soar(artifact_to_dict(artifact))

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
            "flags": list(filter(lambda flag: getattr(message.flags, flag), MESSAGE_FLAGS)) or "no flags",
            "attachments": attachments or "no attachments",
            "embeds": embeds or "no embeds",
            "content": message.content
        }

    async def fetch_guild(self):
        try:
            guild = await self._client.fetch_guild(self._guild_id)
        except discord.HTTPException as e:
            self.save_progress(str(e))
            action_result = self.add_action_result(ActionResult(dict()))
            action_result.set_status(phantom.APP_ERROR, "Fetching the guild failed")
            return None
        return guild

    def _handle_delete_message(self, param):
        self.save_progress("In action handler for: {0}".format(self.get_action_identifier()))
        action_result = self.add_action_result(ActionResult(dict(param)))

        channel_id = param['channel_id']
        message_id = param['message_id']

        message, ret_val = self._async_loop.run_until_complete(self.delete_message(channel_id, message_id))
        self.save_progress("Action on message {} ended with return value of: {}: {}".format(message_id, ret_val, message))

        summary = action_result.update_summary({})
        summary['action result: '] = "Action on message {} ended with return value of: {}: {}".format(message_id, ret_val, message)

        if ret_val != 200:
            return action_result.set_status(phantom.APP_ERROR)
        return action_result.set_status(phantom.APP_SUCCESS)

    async def delete_message(self, channel_id, message_id):
        await self._client.login(self._token)

        guild = await self._client.fetch_guild(self._guild_id)
        channel = await guild.fetch_channel(channel_id)

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound as e:
            self.save_progress("Failed to fetch message, it was deleted already or could not be found: {}".format(e))
            return "Failed to fetch message, it was deleted already or could not be found", 404

        try:
            await message.delete()
        except discord.Forbidden as e:
            self.save_progress("You do not have proper permissions to delete the message: {}".format(e))
            return "Forbidden, you do not have proper permissions to delete the message", 403
        except discord.HTTPException as e:
            self.save_progress("HTTP Exception: {}".format(str(e)))

        await self._client.close()
        return "success", 200

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == 'list_guilds':
            ret_val = self._handle_list_guilds(param)

        if action_id == 'list_channels':
            ret_val = self._handle_list_channels(param)

        if action_id == 'fetch_message':
            ret_val = self._handle_fetch_message(param)

        if action_id == 'delete_message':
            ret_val = self._handle_delete_message(param)

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

        self._headers = {"Authorization": "Bot " + self._token}

        intents = discord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)
        self._async_loop.run_until_complete(self._client.login(self._token))
        self._guild = self._async_loop.run_until_complete(self.fetch_guild())

        return phantom.APP_SUCCESS

    def finalize(self):
        # Save the state, this data is saved across actions and app upgrades
        self._client.close()
        self._async_loop.close()
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
