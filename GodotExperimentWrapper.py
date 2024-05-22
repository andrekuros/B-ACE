import json
import random
import atexit
import time
from godot_rl.core.godot_env import GodotEnv

class GodotExperimentWrapper(GodotEnv):
    
    def __init__(self, config_kwargs):                               
                        
        self.env_config = config_kwargs.get("EnvConfig", "") 
        self.agents_config = config_kwargs.get("AgentsConfig", "")
        self.experiment_config = config_kwargs.get("ExperimentConfig", "")    
        
        #Godot Line Parameters Commands
        self.env_path       = self.env_config.get("env_path", "./bin/BVR.exe")  
        self.show_window    = self.env_config.get("renderize", 1)  
        self._seed          = self.env_config.get("seed", 1)  
        self.action_repeat  = self.env_config.get("action_repeat", 20)  
        self.action_type    = self.env_config.get("action_type", "Low_Level_Continuous")  
        self.speedup        = self.env_config.get("speedup", 1000)                          
        
        self.parallel_envs  = self.env_config.get("parallel_envs", 1)             
        
        self.port = GodotExperimentWrapper.DEFAULT_PORT + random.randint(0,3100)                 
        self.proc = None
        
        if self.env_path is not None and self.env_path != "debug":
            self.env_path = self._set_platform_suffix(self.env_path)

            self.check_platform(self.env_path)  

            self._launch_env(self.env_path, self.port, self.show_window == 1, None, self._seed, self.action_repeat, self.speedup)
        else:
            print("No game binary has been provided, please press PLAY in the Godot editor")
        
        self.connection = self._start_server()
        self.num_envs = None
        
        self._handshake()                
        self.send_sim_config(self.experiment_config)   
        #self._get_env_info()                                    
        
        atexit.register(self._close)
                                        
                            
    def send_sim_config(self, _experiment_config):
        message = {"type": "config"}        
        message["agents_config"] = self.agents_config
        message["env_config"] = self.env_config
        message["experiment_config"] = _experiment_config
        self._send_as_json(message)
        
        
    def watch_experiment(self):
        
        # Wait for the experiment results
        while True:                                   
            
            response = self._check_data()            
            if response["type"] == "experiment_results":                
                #print("Experiment Concluded")
                break
            if response["type"] == "experiment_step":                
                print(f'{str(response["run_finished"])}', end="." )
            time.sleep(1)
                            
        experiment_results = response["results"]        
        return experiment_results
    
    def _check_data(self):
        data = self._get_data_non_blocking()        
        if data != None:
            return data#json.loads(data)
        else:
            return {"type" : None }
    
    def _get_data_non_blocking(self):
        try:
            self.connection.setblocking(False)
            
            # Receive the size (in bytes) of the remaining data to receive
            string_size_bytes: bytearray = bytearray()
            received_length: int = 0

            # The first 4 bytes contain the length of the remaining data
            length: int = 4

            while received_length < length:
                try:
                    data = self.connection.recv(length - received_length)
                    received_length += len(data)
                    string_size_bytes.extend(data)
                except BlockingIOError:
                    # No data available, return a dictionary with "type" set to None
                    self.connection.setblocking(True)
                    return None

            length = int.from_bytes(string_size_bytes, "little")

            # Receive the rest of the data
            string_bytes: bytearray = bytearray()
            received_length = 0

            while received_length < length:
                try:
                    data = self.connection.recv(length - received_length)
                    received_length += len(data)
                    string_bytes.extend(data)
                except BlockingIOError:
                    # No data available, return a dictionary with "type" set to None
                    return {"type": None}

            string: str = string_bytes.decode()

            return json.loads(string)
        except socket.timeout as e:
            print("env timed out", e)
        finally:
            self.connection.setblocking(True)

        return {"type": None}
