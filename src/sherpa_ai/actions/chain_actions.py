from typing import Any

from loguru import logger

from sherpa_ai.actions.base import BaseAction, BaseRetrievalAction
from sherpa_ai.config.task_config import AgentConfig


class ChainActions(BaseAction):
    actions: list[BaseAction]
    instruction: list[dict]

    def execute(self, **kwargs):
        output_list = [[""]]
        for i in range(len(self.actions)):
            kwargs_act = self.instruction[i]
            if i != 0 and len(kwargs_act) != 0:
                for key, value in kwargs_act.items():
                    if "output" not in value.keys():
                        kwargs_act[key] = output_list[value["action"]][0]
                    else:
                        kwargs_act[key] = output_list[value["action"]][value["output"]]
                res = self.actions[i](**kwargs_act)
            elif i != 0 and len(kwargs_act) == 0:
                res = self.actions[i]()
            elif i == 0:
                res = self.actions[i](**kwargs)
            if type(res) is tuple:
                output_list.append([it_res for it_res in res])
            else:
                output_list.append([res])
        return self.actions[-1](**kwargs_act)
