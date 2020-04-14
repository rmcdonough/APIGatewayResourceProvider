import logging
from typing import Any, MutableMapping, Optional

from cloudformation_cli_python_lib import (
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

resource = Resource(TYPE_NAME, ResourceModel)
test_entrypoint = resource.test_entrypoint


class APIGateway(object):
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
        logging.warning('Response from create_api: ' + str(create_response))
        return {
            'restApiId': create_response['id'],
            'RootResourceId': self._get_root_resource_id(create_response['id'])
        }

    def delete_api(self, name):
        """Deletes an API Gateway"""
        response = self.client.delete_rest_api(restApiId=name)
        logging.warning('Response from delete_api: ' + str(response))
        return response

    def get_api(self, restApiId):
        """Returns information about an API"""
        api_response = self.client.get_rest_api(restApiId=restApiId)
        response = {
            'restApiId': api_response['id'],
            'Name': api_response['name'],
            'Description': api_response['description'],
            'apiKeySource': api_response['apiKeySource'],
            'endpointConfiguration': api_response['endpointConfiguration'],
            'tags': api_response['tags'],
            'RootResourceId': self._get_root_resource_id(restApiId)
        }
        logging.warning('Returning response from api_response: ' + str(response))
        return response

    def _get_root_resource_id(self, restApiId):
        """Returns the ID of the root resource (/)"""
        # todo: make resource_response paginator safe
        resource_response = self.client.get_resources(restApiId=restApiId)
        logging.warning('Response from get_root_resource_id: ' + str(resource_response))
        for item in resource_response['items']:
            if item['path'] == '/':
                logging.warning('root item found: ' + item['id'])
                return item['id']


@resource.handler(Action.CREATE)
def create_handler(session: Optional[SessionProxy],
                   request: ResourceHandlerRequest,
                   callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    try:
        api = APIGateway(session)
        response = api.create_api(model.Name, model.Description)
        model.restApiId = response['restApiId']
        model.RootResourceId = response['RootResourceId']
        logging.warning(str(model))
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message=str(model))


@resource.handler(Action.DELETE)
def delete_handler(session: Optional[SessionProxy],
                   request: ResourceHandlerRequest,
                   callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    try:
        api = APIGateway(session)
        response = api.delete_api(model.restApiId)
        model.message = response
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='DeleteOK')


@resource.handler(Action.READ)
def read_handler(session: Optional[SessionProxy],
                 request: ResourceHandlerRequest,
                 callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    try:
        api = APIGateway(session)
        response = api.get_api(model.restApiId)
        model.message = response
        model.RootResourceId = response['RootResourceId']
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    logging.warning('Resource model in read_handler: ' + str(model))
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='ReadOK')
