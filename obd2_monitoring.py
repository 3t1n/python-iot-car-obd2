import obd
import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from datetime import datetime
from azure.eventhub import EventHubProducerClient, EventData
from azure.eventhub.exceptions import EventHubError
import queue
import geocoder  # Para GPS
import random

class OBD2GUI:
    def __init__(self, root, simulation_mode=False):
        self.root = root
        self.root.title("Monitor OBD2")
        self.root.geometry("400x500") 
        
        # Modo de simulação
        self.simulation_mode = simulation_mode
        
        # Fila para mensagens de log
        self.log_queue = queue.Queue()
        
        # Estilo
        style = ttk.Style()
        style.configure("Value.TLabel", font=("Arial", 24))
        style.configure("Title.TLabel", font=("Arial", 12))
        
        # Frames para dados
        self.create_sensor_frame("RPM", 0)
        self.create_sensor_frame("Velocidade (km/h)", 1)
        self.create_sensor_frame("Temperatura Motor (°C)", 2)
        
        # Frame GPS
        self.gps_label = ttk.Label(root, text="GPS: Buscando...", font=("Arial", 12))
        self.gps_label.pack(pady=10)
        
        # Configurações do Event Hub
        self.connection_string = "<coloque sua connection string do event hub>"
        self.eventhub_name = "<coloque o nome do seu event hub>"
        
        # Criar produtor do Event Hub
        try:
            self.producer = EventHubProducerClient.from_connection_string(
                conn_str=self.connection_string,
                eventhub_name=self.eventhub_name
            )
            print("Conectado ao Event Hub com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar ao Event Hub: {e}")
            self.producer = None
        
        # Status da conexão
        if self.simulation_mode:
            self.status_label = ttk.Label(root, text="✓ Modo Simulação", foreground="blue")
        else:
            try:
                self.connection = obd.OBD('/dev/tty.OBDII') #Aqui procure em que porta está se conectando seu OBD2 ao seu computador e troque o parametro da função, esse /dev/tty.OBDII é o meu caso
                self.status_label = ttk.Label(root, 
                    text="✓ Conectado" if self.connection.is_connected() else "✗ Desconectado",
                    foreground="green" if self.connection.is_connected() else "red")
            except:
                self.connection = None
                self.status_label = ttk.Label(root, text="Erro de conexão OBD", foreground="red")
        
        self.status_label.pack(pady=5)
        
        # Log de eventos
        self.log_text = tk.Text(root, height=5, wrap=tk.WORD)
        self.log_text.pack(fill="x", padx=10, pady=5)
        
        # Iniciar threads
        self.running = True
        threading.Thread(target=self.update_values, daemon=True).start()
        threading.Thread(target=self.update_gps, daemon=True).start()
        
        # Iniciar processamento de log
        self.process_log_queue()

    def create_sensor_frame(self, title, row):
        frame = ttk.Frame(self.root)
        frame.pack(pady=5, fill="x", padx=20)
        
        title_label = ttk.Label(frame, text=title, style="Title.TLabel")
        title_label.pack()
        
        value_label = ttk.Label(frame, text="--", style="Value.TLabel")
        value_label.pack()
        
        setattr(self, f"{title.split()[0].lower()}_label", value_label)

    def send_to_eventhub(self, data):
        if not self.producer:
            self.queue_log_message("✗ Sem conexão com Event Hub")
            return

        try:
            batch = self.producer.create_batch()
            batch.add(EventData(json.dumps(data)))
            self.producer.send_batch(batch)
            self.queue_log_message("✓ Dados enviados para Event Hub")
        except Exception as e:
            self.queue_log_message(f"✗ Erro ao enviar dados: {str(e)}")

    def queue_log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def process_log_queue(self):
        """Processa mensagens de log na thread principal"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert("1.0", message)
                self.log_text.see("1.0")
        except queue.Empty:
            pass
        finally:
            if self.running:
                self.root.after(100, self.process_log_queue)

    def simulate_obd_data(self):
        """Gera dados simulados do OBD"""
        return {
            'rpm': random.randint(800, 3500),
            'velocidade': random.randint(0, 120),
            'temperatura': random.randint(80, 95)
        }

    def simulate_gps(self):
        """Gera dados GPS simulados (área de São Paulo)"""
        # Coordenadas base de São Paulo
        base_lat = -23.550520
        base_lon = -46.633308
        
        # Adiciona uma pequena variação aleatória
        lat = base_lat + random.uniform(-0.1, 0.1)
        lon = base_lon + random.uniform(-0.1, 0.1)
        
        return {
            'latitude': lat,
            'longitude': lon
        }

    def update_values(self):
        if not self.simulation_mode and not self.connection:
            return
            
        commands = {
            'rpm': obd.commands.RPM,
            'velocidade': obd.commands.SPEED,
            'temperatura': obd.commands.COOLANT_TEMP
        }
        
        while self.running:
            data = {
                "timestamp": datetime.now().isoformat(),
                "device_id": "TIIDA_2011",
                "rpm": None,
                "velocidade": None,
                "temperatura": None,
                "latitude": None,
                "longitude": None
            }
            
            if self.simulation_mode:
                # Dados OBD2 simulados
                simulated_obd = self.simulate_obd_data()
                data.update(simulated_obd)
                
                # GPS simulado
                simulated_gps = self.simulate_gps()
                data.update(simulated_gps)
                
                # Atualiza interface
                for name, value in simulated_obd.items():
                    self.root.after(0, self.update_label, name, value)
                
                # Atualiza GPS na interface
                self.root.after(0, self.gps_label.config, 
                    {"text": f"GPS: {data['latitude']:.4f}, {data['longitude']:.4f}"})
            else:
                # Dados OBD2 reais
                for name, cmd in commands.items():
                    try:
                        response = self.connection.query(cmd)
                        if not response.is_null():
                            value = response.value.magnitude
                            data[name] = value
                            self.root.after(0, self.update_label, name, value)
                    except Exception as e:
                        print(f"Erro ao ler {name}: {e}")
                
                # GPS real
                try:
                    g = geocoder.ip('me')
                    if g.ok:
                        data["latitude"] = g.latlng[0]
                        data["longitude"] = g.latlng[1]
                        self.root.after(0, self.gps_label.config, 
                            {"text": f"GPS: {g.latlng[0]:.4f}, {g.latlng[1]:.4f}"})
                except Exception as e:
                    print(f"Erro ao obter GPS: {e}")
            
            # Só envia se tiver RPM válido
            if data["rpm"] is not None:
                self.send_to_eventhub(data)
                self.queue_log_message("✓ Dados enviados com RPM válido")
            else:
                self.queue_log_message("✗ Dados não enviados - RPM ausente")
            
            time.sleep(1)

    def update_label(self, name, value):
        """Atualiza labels na thread principal"""
        label = getattr(self, f"{name}_label")
        label.config(text=f"{value:.0f}")

    def update_gps(self):
        while self.running:
            try:
                if self.simulation_mode:
                    lat, lon = self.simulate_gps()
                else:
                    g = geocoder.ip('me')
                    if g.ok:
                        lat, lon = g.latlng
                    else:
                        raise Exception("Não foi possível obter localização")
                
                # Atualizar label do GPS
                self.root.after(0, self.gps_label.config, 
                    {"text": f"GPS: {lat:.4f}, {lon:.4f}"})
                
                # Adicionar ao próximo conjunto de dados
                self.current_gps = {'latitude': lat, 'longitude': lon}
                
            except Exception as e:
                self.root.after(0, self.gps_label.config, 
                    {"text": f"GPS: Erro ({str(e)})"})
                self.current_gps = None
            
            time.sleep(5)  # Atualiza a cada 5 segundos

    def on_closing(self):
        self.running = False
        if self.producer:
            self.producer.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Para rodar em modo de simulação, mude para True
    simulation_mode = True  # Mude para False para usar dados reais
    app = OBD2GUI(root, simulation_mode)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
