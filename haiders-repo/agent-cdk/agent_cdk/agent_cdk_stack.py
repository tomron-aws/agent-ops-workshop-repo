from aws_cdk import (
   Stack,
   aws_lambda as lambda_,
   aws_iam as iam,
   CfnResource,
   Duration
)
from cdklabs.generative_ai_cdk_constructs import bedrock
from constructs import Construct
import json


class YfinStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.create_stock_info_agent()
        self.create_stock_news_agent()
        self.create_market_indices_agent()
        self.create_crypto_agent()
        self.create_bonds_agent()
        self.create_futures_agent()
        self.create_etf_agent()
        self.create_mutual_funds_agent()
        self.create_forex_agent()
        self.create_sectors_agent()
        self.create_projections_agent()  # Add this line
        
    def create_lambda_reference(self, id_name: str) -> lambda_.IFunction:
        return lambda_.Function.from_function_attributes(
            self, 
            id_name,
            function_arn="arn:aws:lambda:us-west-2:239122513475:function:yfin-api-ApiFunction-TAdCCmJLi062",
            same_environment=True
    )
    
    def create_stock_info_agent(self):
        
        agent = bedrock.Agent(
            self,
            "stock_info_agent",
            name="stock_info_agent",
            description="You are a Financial Market Analyst Assistant that helps customers stocks and day's stock performance.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/stock_info_agent.txt").read().strip(),
        )
        
        
        stock_info: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="stock_info_service",
            description="Get stock's symbol details",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("stock_info_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/stock_info.json"),  
        )
        agent.add_action_group(stock_info)
        
        stock_list: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="stock_list_service",
            description="Stock list for Days performance",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("stock_list_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/stock_list_service.json"),  
        )
        agent.add_action_group(stock_list)
        
        stock_financials: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="stock_financials",
            description="stock_financials balance sheet, cash flow, income statement and news API",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("stock_financials_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/stock_financials.json"),  
        )
        agent.add_action_group(stock_financials)
                


    def create_stock_news_agent(self):
        
        agent = bedrock.Agent(
            self,
            "stock_news_agent",
            name="stock_news_agent",
            description="Stock news Analyst Assistant that helps customers understand stocks news.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/stock_news_agent.txt").read().strip(),
        )
        
        
        stock_news: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="stock_news",
            description="Get stock news for given symbol",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("stock_news_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/stock_news.json"),  
        )
        agent.add_action_group(stock_news)
                



    def create_market_indices_agent(self):
        
        agent = bedrock.Agent(
            self,
            "market_indices",
            name="market_indices_agent",
            description="Financial Market Analyst Assistant that helps customers understand financial Markets indies performance.",
            should_prepare_agent=True,	
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/market_indices_agent.txt").read().strip(),
        )
        
        
        market_indices: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="market_indices_service",
            description="Market Indices covering the world",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("market_indices_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/market_indices.json"),  
        )
        agent.add_action_group(market_indices)

    def create_crypto_agent(self):
        
        agent = bedrock.Agent(
            self,
            "crypto_agent",
            name="crypto_agent",
            description="Cryptocurrencies Analyst Assistant that helps customers understand Crypto choices.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/crypto_agent.txt").read().strip(),
        )
        
        
        crypto_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="crypto_service",
            description="Cryptocurrencies performance",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("crypto_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/crypto_service.json"),  
        )
        agent.add_action_group(crypto_service)

    def create_bonds_agent(self):
        
        agent = bedrock.Agent(
            self,
            "bonds_agent",
            name="bonds_agent",
            description="Bonds Analyst Assistant that helps customers understand Bonds choices.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/bonds_agent.txt").read().strip(),
        )
        
        
        bonds_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="bonds_service",
            description="markets bonds performanc",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("bonds_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/bonds_service.json"),  
        )
        agent.add_action_group(bonds_service)

    def create_futures_agent(self):
        
        agent = bedrock.Agent(
            self,
            "futures_agent",
            name="futures_agent",
            description="Futures contract Analyst Assistant that helps customers understand Futures choices.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/futures_agent.txt").read().strip(),
        )
        
        
        futures_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="futures_service",
            description="Futures contracts performance",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("futures_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/futures_service.json"),  
        )
        agent.add_action_group(futures_service)


    def create_etf_agent(self):
        
        agent = bedrock.Agent(
            self,
            "etf_agent",
            name="etf_agent",
            description="ETF Market Analyst Assistant that helps customers understand ETF choices.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/etf_agent.txt").read().strip(),
        )
        
        
        etf_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="etf_service",
            description="ETF performance",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("etf_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/etf_service.json"),  
        )
        agent.add_action_group(etf_service)


    def create_mutual_funds_agent(self):
        
        agent = bedrock.Agent(
            self,
            "mutual_funds_agent",
            name="mutual_funds_agent",
            description="Mutual funds Analyst Assistant that helps customers understand Mutual funds.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/mutual_funds_agent.txt").read().strip(),
        )
        
        
        etf_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="mutual_funds_service",
            description="Mutual funds performance",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("mutual_funds_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/mutual_funds_service.json"),  
        )
        agent.add_action_group(etf_service)
        
    def create_projections_agent(self):
        
        agent = bedrock.Agent(
            self,
            "projections_agent",
            name="projections_agent",
            description="Financial Projections Assistant that helps customers understand their future account values.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/projections_agent.txt").read().strip(),
        )
        
        
        projections_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="projections_service",
            description="Account value projections",
            executor= bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("projections_service_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/projections_service.json"),  
        )
        agent.add_action_group(projections_service)

    def create_forex_agent(self):
        """
        Creates a Forex agent with Bedrock integration
        """
        agent = bedrock.Agent(
            self,
            "forex_agent",
            name="forex_agent",
            description="Forex Market Analyst Assistant that helps customers understand currency market performance.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/forex_agent.txt").read().strip(),
        )
        
        forex_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="forex_service",
            description="Forex market performance",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("forex_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/forex_service.json"),
        )
        agent.add_action_group(forex_service)


    def create_sectors_agent(self):
        """
        Creates a Sectors Analysis agent with Bedrock integration
        """
        agent = bedrock.Agent(
            self,
            "sectors_agent",
            name="sectors_agent",
            description="Sectors Analysis Assistant that helps customers understand market sectors and their performance.",
            should_prepare_agent=True,
            foundation_model=bedrock.BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_HAIKU_V1_0,
            instruction=open("../instructions/sector_agent.txt").read().strip(),
        )
        
        sector_service: bedrock.AgentActionGroup = bedrock.AgentActionGroup(
            name="sectors_service",
            description="Market sectors performance and analysis",
            executor=bedrock.ActionGroupExecutor.fromlambda_function(self.create_lambda_reference("sector_lambda")),
            enabled=True,
            api_schema=bedrock.ApiSchema.from_local_asset("../open_api_schema/sector_service.json"),  
        )
        agent.add_action_group(sector_service)
            