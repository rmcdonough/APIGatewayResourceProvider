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

    def list_apis(self):
        """Returns the list of API Gateways"""
        return self.apis

    def create_api(self, name, description):
        """Create a new private API Gateway"""
        # Throw an error if we are trying to reuse an existing name
        if name in self.apis:
            # todo: this can be handled much cleaner with a better error message indicating a duplicate
            raise NameError

        # First we create the new API
        create_response = self.client.create_rest_api(
            name=name,
            description=description,
            endpointConfiguration={'types': ['PRIVATE']},
            tags={'CreatedBy': TYPE_NAME}
        )

        # And now we get the ID for the root resource (/)
        resource_response = self.client.get_resources(restApiId=create_response['id'])
        return {
            'restApiId': create_response['id'],
            'RootResourceId': resource_response['items'][0]['id']
        }

    def delete_api(self, name):
        """Deletes an API Gateway"""
        response = self.client.delete_rest_api(restApiId=name)
        return response

    def get_api(self, restApiId):
        """Returns information about an API"""
        response = self.client.get_rest_api(restApiId=restApiId)
        return response


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
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model, message='ReadOK')
