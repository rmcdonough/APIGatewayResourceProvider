# SLF::APIGateway::Private

Congratulations on starting development! Next steps:

1. Write the JSON schema describing your resource, `slf-apigateway-private.json`
2. Implement your resource handlers in `slf_apigateway_private/handlers.py`

> Don't modify `models.py` by hand, any modifications will be overwritten when the `generate` or `package` commands are run.

Implement CloudFormation resource here. Each function must always return a ProgressEvent.

```python
ProgressEvent(
    # Required
    # Must be one of OperationStatus.IN_PROGRESS, OperationStatus.FAILED, OperationStatus.SUCCESS
    status=OperationStatus.IN_PROGRESS,
    # Required on SUCCESS (except for LIST where resourceModels is required)
    # The current resource model after the operation; instance of ResourceModel class
    resourceModel=model,
    resourceModels=None,
    # Required on FAILED
    # Customer-facing message, displayed in e.g. CloudFormation stack events
    message="",
    # Required on FAILED: a HandlerErrorCode
    errorCode=HandlerErrorCode.InternalFailure,
    # Optional
    # Use to store any state between re-invocation via IN_PROGRESS
    callbackContext={},
    # Required on IN_PROGRESS
    # The number of seconds to delay before re-invocation
    callbackDelaySeconds=0,
)
```

Failures can be passed back to CloudFormation by either raising an exception from `cloudformation_cli_python_lib.exceptions`, or setting the ProgressEvent's `status` to `OperationStatus.FAILED` and `errorCode` to one of `cloudformation_cli_python_lib.HandlerErrorCode`. There is a static helper function, `ProgressEvent.failed`, for this common case.

## What's with the type hints?

We hope they'll be useful for getting started quicker with an IDE that support type hints. Type hints are optional - if your code doesn't use them, it will still work.


# mcdrich@ notes

Deploying:

```bash
aws cloudformation create-stack --stack-name apigateway-test --template-body file://test-stack/apigateway.yaml --parameters ParameterKey=APIName,ParameterValue=APIGatewayTest ParameterKey=APIDescription,ParameterValue="API Gateway Test"
```

Deleting:

```bash
aws cloudformation delete-stack --stack-name apigateway-test
```

A sample policy has been placed into test-stack/sample-iam-user-policy.json as well