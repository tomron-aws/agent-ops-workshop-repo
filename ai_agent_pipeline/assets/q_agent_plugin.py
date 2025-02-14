# q_agent_plugin = CfnResource(
        #     self, "AIAgentPlugin",
        #     type="AWS::QBusiness::Plugin",
        #     properties={
        #         "ApplicationId" : q_agent.ref,
        #         "AuthConfiguration" : {
        #             "NoAuthConfiguration": {}
        #         },
        #         "CustomPluginConfiguration" : {
        #             "ApiSchema" : {
                        
        #                 "Payload" : """{
        #                     "openapi": "3.0.0",
        #                     "info": {
        #                         "title": "FastAPI",
        #                         "version": "0.1.0"
        #                     },
        #                     "servers": [
        #                         {
        #                         "url": "https://dj3a2w5zbcgq8.cloudfront.net"
        #                         }
        #                     ],
        #                     "paths": {
        #                         "/api/chat/": {
        #                         "post": {
        #                             "tags": [
        #                             "chat_router"
        #                             ],
        #                             "summary": "Chat",
        #                             "description": "This API is used by a Financial Analyst  to provide clients' financial goals, stock information and S&P 500 and DOW Jones reqlated queries.The API interacts with SearchClient, ClientList, ClientDetail, StockInfo, Index_Tickers, GoalServicePopularGoals",
        #                             "operationId": "chat_api_chat__post",
        #                             "requestBody": {
        #                             "content": {
        #                                 "application/json": {
        #                                 "schema": {
        #                                     "$ref": "#/components/schemas/ChatRequest"
        #                                 }
        #                                 }
        #                             },
        #                             "required": true
        #                             },
        #                             "responses": {
        #                             "200": {
        #                                 "description": "Successful Response",
        #                                 "content": {
        #                                 "application/json": {
        #                                     "schema": {
        #                                     "$ref": "#/components/schemas/ChatResponse"
        #                                     }
        #                                 }
        #                                 }
        #                             },
        #                             "422": {
        #                                 "description": "Validation Error",
        #                                 "content": {
        #                                 "application/json": {
        #                                     "schema": {
        #                                     "$ref": "#/components/schemas/HTTPValidationError"
        #                                     }
        #                                 }
        #                                 }
        #                             }
        #                             }
        #                         }
        #                         }
        #                     },
        #                     "components": {
        #                         "schemas": {
        #                         "ChatRequest": {
        #                             "type": "object",
        #                             "title": "ChatRequest",
        #                             "properties": {
        #                             "prompt": {
        #                                 "type": "string",
        #                                 "title": "Prompt"
        #                             }
        #                             },
        #                             "required": [
        #                             "prompt"
        #                             ]
        #                         },
        #                         "ChatResponse": {
        #                             "type": "object",
        #                             "title": "ChatResponse",
        #                             "properties": {
        #                             "response": {
        #                                 "type": "string",
        #                                 "title": "Response"
        #                             }
        #                             },
        #                             "required": [
        #                             "response"
        #                             ]
        #                         },
        #                         "HTTPValidationError": {
        #                             "type": "object",
        #                             "title": "HTTPValidationError",
        #                             "properties": {
        #                             "detail": {
        #                                 "type": "array",
        #                                 "title": "Detail",
        #                                 "items": {
        #                                 "$ref": "#/components/schemas/ValidationError"
        #                                 }
        #                             }
        #                             }
        #                         },
        #                         "ValidationError": {
        #                             "type": "object",
        #                             "title": "ValidationError",
        #                             "properties": {
        #                             "loc": {
        #                                 "type": "array",
        #                                 "title": "Location",
        #                                 "items": {
        #                                 "anyOf": [
        #                                     {
        #                                     "type": "string"
        #                                     },
        #                                     {
        #                                     "type": "integer"
        #                                     }
        #                                 ]
        #                                 }
        #                             },
        #                             "msg": {
        #                                 "type": "string",
        #                                 "title": "Message"
        #                             },
        #                             "type": {
        #                                 "type": "string",
        #                                 "title": "Error Type"
        #                             }
        #                             },
        #                             "required": [
        #                             "loc",
        #                             "msg",
        #                             "type"
        #                             ]
        #                         }
        #                         }
        #                     }
        #                     }"""
        #             },
        #             "ApiSchemaType" : "OPEN_API_V3",
        #             "Description" : "plugin description"
        #         },
        #         "DisplayName" : "q-biz-plugin",
        #         "Type" : "CUSTOM"
        #     }
        # )