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

        #
        # todo: make paginator safe
        #

        self.apis = []
        apis = self.client.get_rest_apis()
        for api_id in apis['items']:
            self.apis.append(api_id['name'])

    def list_apis(self):
        """Returns the list of API Gateways"""
        return self.apis

    def create_api(self, name, description):
        """
        Create a new API Gateway

        The endpoint configuration is hard coded to be PRIVATE
        """
        # Throw an error if we are trying to reuse an existing name
        if name in self.apis:
            raise NameError
        response = self.client.create_rest_api(
            name=name,
            description=description,
            endpointConfiguration={'types': ['PRIVATE']},
            tags={
                'CreatedBy': 'SLF::APIGateway::Private'
            }
        )
        return response

    def delete_api(self, name):
        """Deletes an API Gateway"""
        response = self.client.delete_rest_api(restApiId=name)
        return response

    def get_api(self, name):
        """Returns information about an API"""
        response = self.client.get_rest_api(restApiId=name)
        return response


@resource.handler(Action.CREATE)
def create_handler(session: Optional[SessionProxy],
                   request: ResourceHandlerRequest,
                   callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(status=OperationStatus.IN_PROGRESS, resourceModel=model)
    try:
        api = APIGateway(session)
        response = api.create_api(model.Name, model.Description)
        progress.status = OperationStatus.SUCCESS
        progress.resourceModel = {'restApiId': response['id'], 'Response': response}
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return progress


@resource.handler(Action.UPDATE)
def update_handler(session: Optional[SessionProxy],
                   request: ResourceHandlerRequest,
                   callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    #
    # todo: the update handler is just a stub for now
    #

    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    progress.status = OperationStatus.SUCCESS
    return progress


@resource.handler(Action.DELETE)
def delete_handler(session: Optional[SessionProxy],
                   request: ResourceHandlerRequest,
                   callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    try:
        api = APIGateway(session)
        response = api.delete_api(model.Name)
        progress.status = OperationStatus.SUCCESS
        progress.resourceModel = {'Response': response}
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return progress


@resource.handler(Action.READ)
def read_handler(session: Optional[SessionProxy],
                 request: ResourceHandlerRequest,
                 callback_context: MutableMapping[str, Any]) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    try:
        api = APIGateway(session)
        response = api.get_api(model.Name)
        progress.status = OperationStatus.SUCCESS
        progress.resourceModel = {'Response': response}
    except TypeError as e:
        raise exceptions.InternalFailure(f"was not expecting type {e}")
    return progress

#
# @resource.handler(Action.LIST)
# def list_handler(
#     session: Optional[SessionProxy],
#     request: ResourceHandlerRequest,
#     callback_context: MutableMapping[str, Any],
# ) -> ProgressEvent:
#     # TODO: put code here
#     return ProgressEvent(
#         status=OperationStatus.SUCCESS,
#         resourceModels=[],
#     )
