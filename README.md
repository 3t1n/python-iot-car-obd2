# Monitoramento seu carro com Python e Power BI

Visão Geral

Este projeto tem como objetivo capturar dados da ECU (Unidade de Controle Eletrônico) de um veículo através do protocolo OBD2 utilizando um módulo ELM via Bluetooth. Os dados são coletados por um script Python e enviados em tempo real para um pipeline de streaming utilizando Azure Event Hubs e Eventstream. Em seguida, os dados são armazenados no Eventhouse para posterior visualização em um dashboard em tempo real.

Arquitetura do Projeto

Scanner OBD2: Conectado à porta OBD2 do veículo (exemplo: Nissan Tiida).

Script Python: Captura as informações do módulo ELM via Bluetooth.

Azure Event Hubs: Recebe os dados em streaming.

Eventstream: Fluxo de processamento de eventos no Data Fabric.

Eventhouse: Banco de dados de eventos para persistência dos dados.

Dashboard em Tempo Real: Consome os dados armazenados no Eventhouse para visualização.

Tecnologias Utilizadas

Python: Para captura e envio dos dados.

ELM327 Bluetooth: Scanner OBD2.

Azure Event Hubs: Para transmissão dos dados.

Eventstream (Data Fabric): Processamento dos eventos.

Eventhouse: Armazenamento dos dados.

Dashboard em Tempo Real: Visualização dos dados.

Como Executar o Projeto

1. Configurar o Scanner OBD2

Conecte o dispositivo OBD2 na porta do veículo.

Pareie o scanner via Bluetooth com o computador.

2. Instalar Dependências

Certifique-se de que possui o Python instalado e instale as dependências necessárias:

pip install pyobd pyserial azure-eventhub

3. Configurar o Script Python

Edite o arquivo obd2_monitoring.py para adicionar as credenciais do Azure Event Hubs:

EVENT_HUB_CONNECTION_STRING = "sua_connection_string"
EVENT_HUB_NAME = "seu_event_hub"

4. Executar o Script

Execute o script para iniciar a coleta de dados:

python obd2_monitoring.py

Os dados serão coletados do veículo e enviados para o Azure Event Hubs.

5. Configurar o Eventstream e Eventhouse

Configure um fluxo no Eventstream para processar os dados do Event Hubs.

Configure o Eventhouse para armazenar os dados processados.

6. Criar o Dashboard em Tempo Real

Utilize uma ferramenta como Power BI, Grafana ou outra para conectar ao Eventhouse e visualizar os dados em tempo real.

Exemplo de Saída

RPM: 1196
Velocidade (km/h): 45
Temperatura Motor (°C): 84
GPS: -23.5074, -46.6965

Contribuição

Sinta-se à vontade para contribuir com melhorias no projeto!

Licença

Este projeto está licenciado sob a GNU General Public License (GPL) v3.0 .
