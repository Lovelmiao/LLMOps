import json
import os
from typing import Type, Any

import dotenv
import requests
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


dotenv.load_dotenv()

class GoogleSerperArgsSchema(BaseModel):
    query: str = Field(description="需要查询的搜索语句，例如：python官网")

class GaodeWeatherArgsSchema(BaseModel):
    city: str = Field(description="需要查询天气的目标城市，例如：北京")

class GaodeWeatherTool(BaseTool):
    '''查询高德天气预报工具'''
    name: str = "gaode_weather"
    description: str = "查询高德天气预报"
    args_schema: Type[BaseModel] = GaodeWeatherArgsSchema

    def _run(self, *args: Any, **kwargs: Any) -> str:
        gaode_api_key = os.getenv("GAODE_API_KEY")
        if not gaode_api_key:
            return f'请设置环境变量GAODE_API_KEY以使用高德天气预报工具'

        city = kwargs.get("city", "")
        api_domain = "https://restapi.amap.com/v3"
        session = requests.Session()

        city_response = session.request(
            url = f'{api_domain}/config/district?key={gaode_api_key}&keywords={city}',
            headers = {"Content-Type": "application/json, charset = utf-8"},
            method = "GET"
        )
        city_response.raise_for_status()
        city_data = city_response.json()
        if city_data.get("status") == "1":
            ad_code = city_data.get("districts")[0].get("adcode")
            weather_response = session.request(
                url=f'{api_domain}/weather/weatherInfo?key={gaode_api_key}&city={ad_code}&extensions=all',
                headers={"Content-Type": "application/json, charset = utf-8"},
                method="GET"
            )

            weather_response.raise_for_status()
            weather_data = weather_response.json()
            if weather_data.get("status") == "1":
                return json.dumps(weather_data)
            else:
                return f'查询天气信息失败，错误信息：{weather_data.get("info", "未知错误")}'
        else:
            return f'查询城市信息失败，错误信息：{city_data.get("info", "未知错误")}'



google_serper = GoogleSerperRun(
    name = "google_serper",
    description = "使用Google Serper API进行搜索",
    args_schema = GoogleSerperArgsSchema,
    api_wrapper = GoogleSerperAPIWrapper()
)

gaode_tool = GaodeWeatherTool()

tools = [google_serper, gaode_tool]


model = ChatOpenAI(
    model="bailu-2.7",
    base_url=os.getenv("BASE_URL")
)

agent = create_agent(tools=tools, model=model)

print(agent.invoke({"messages":[("human", "")]}))
