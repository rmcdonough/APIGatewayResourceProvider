"""Handlers for the API Gateway Resource Provider"""

import logging
from typing import Any, MutableMapping, Optional

from cloudformation_cli_python_lib import (  # pylint: disable=W0611,E0401
    Action,
    HandlerErrorCode,
    OperationStatus,
    ProgressEvent,
    Resource,
    SessionProxy,
    exceptions,
)

from .models import ResourceHandlerRequest, ResourceModel

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)
TYPE_NAME = "SLF::APIGateway::Private"

resource = Resource(TYPE_NAME, ResourceModel)  # pylint: disable=C0103
test_entrypoint = resource.test_entrypoint  # pylint: disable=C0103


class APIGateway():
    """Wrapper for calls to our API Gateway"""
    def __init__(self, session):
        self.client = session.client('apigateway')
        # todo: make paginator safe
        self.apis = []
        apis = self.client.get_rest_apis()
        for api_id in apis['items']:
            self.apis.append(api_id['name'])

    def create_api(self, name, description):
        """Create a new private API Gateway"""
        if name in self.apis:
            # todo: this can be handled much cleaner with a better error message indicating a duplicate
            raise NameError
        create_response = self.client.create_rest_api(
            name=name,
            description=description,
            endpointConfiguration={'types': ['PRIVATE']},
            tags={'CreatedBy': TYPE_NAME}
        )
        logging.warning('Response from create_api: %s', str(create_response))
        return {
            'restApiId': create_response['id'],
            'RootResourceId': self._get_root_resource_id(create_response['id'])
        }

    def delete_api(self, name):
        """Deletes an API Gateway"""
        response = self.client.delete_rest_api(restApiId=name)
        logging.warning('Response from delete_api: %s', str(response))
        return response

    def get_api(self, rest_api_id):
        """Returns information about an API"""
        api_response = self.client.get_rest_api(restApiId=rest_api_id)
        response = {
            'restApiId': api_response['id'],
            'Name': api_response['name'],
            'Description': api_response['description'],
            'apiKeySource': api_response['apiKeySource'],
            'endpointConfiguration': api_response['endpointConfiguration'],
            'tags': api_response['tags'],
            'RootResourceId': self._get_root_resource_id(rest_api_id)
        }
        logging.warning('Returning response from api_response: %s', str(response))
        return response

    def _get_root_resource_id(self, rest_api_id):
        """Returns the ID of the root resource (/)"""
        # todo: make resource_response paginator safe
        resource_response = self.client.get_resources(restApiId=rest_api_id)
        logging.warning('Response from get_root_resource_id: %s', str(resource_response))
        # for item in resource_response['items']:
        #     if item['path'] == '/':
        #         return item['id']
        return [item['id'] for item in resource_response['items'] if item['path'] == "/"][0]


@resource.handler(Action.CREATE)
def create_handler(
        session: Optional[SessionProxy],
        request: ResourceHandlerRequest,
        callback_context: MutableMapping[str, Any]  # pylint: disable=W0613
) -> ProgressEvent:
    """Create function called by CloudFormation"""
    model = request.desiredResourceState
    api = APIGateway(session)
    response = api.create_api(model.Name, model.Description)
    logging.warning('Response from create_api: %s', str(response))
    model.restApiId = response['restApiId']
    model.RootResourceId = response['RootResourceId']
    logging.warning('Response model in create_handler: %s', str(model))
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='CreateOK')


@resource.handler(Action.DELETE)
def delete_handler(
        session: Optional[SessionProxy],
        request: ResourceHandlerRequest,
        callback_context: MutableMapping[str, Any]  # pylint: disable=W0613
) -> ProgressEvent:
    """Delete function called by CloudFormation"""
    model = request.desiredResourceState
    api = APIGateway(session)
    response = api.delete_api(model.restApiId)
    logging.warning('Response from delete_handler: %s', str(response))
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='DeleteOK')


@resource.handler(Action.READ)
def read_handler(
        session: Optional[SessionProxy],
        request: ResourceHandlerRequest,
        callback_context: MutableMapping[str, Any]  # pylint: disable=W0613
) -> ProgressEvent:
    """Read function called by CloudFormation"""
    model = request.desiredResourceState
    api = APIGateway(session)
    response = api.get_api(model.restApiId)
    model.message = response
    model.RootResourceId = response['RootResourceId']
    logging.warning('Resource model in read_handler: %s}', str(model))
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='ReadOK')
