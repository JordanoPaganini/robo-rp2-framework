# Utilizando o GY33

## Construtor

### class gy33_i2c.GY33_I2C(i2c, addr=90)

* i2c: Um objeto I2C  
* addr: Endereço do dispositivo I2C (padrão 90)

## Métodos

### GY33_I2C.read_all()

Retorna uma tupla contendo os valores "Raw Red, Raw Green, Raw Blue, Clear, Lux, Temperatura de Cor, Red, Green, Blue, Color".

O valor "Color" deve ser interpretado da seguinte forma:

| Bit | Cor         |
|------|-------------|
| 7    | Azul        |
| 6    | Azul Marinho|
| 5    | Verde       |
| 4    | Preto       |
| 3    | Branco      |
| 2    | Rosa        |
| 1    | Amarelo     |
| 0    | Vermelho    |

Note que somente os valores Raw e Clear vêm do sensor TCS3472, enquanto os outros valores são derivados dos valores raw pelo microcontrolador embutido.

### GY33_I2C.read_raw()

Retorna uma tupla contendo apenas os valores "Raw Red, Raw Green, Raw Blue, Clear".

Isso economiza leituras se você não precisar dos valores processados.

### GY33_I2C.read_calibrated()

Retorna uma tupla contendo apenas os valores calibrados Red, Green, Blue e Clear.  
Os valores calibrados normalmente ficam entre 0 e 255, mas podem ultrapassar esse intervalo se expostos a níveis de luz acima da calibração.

Essa calibração usa os valores armazenados no objeto gy33, e não são os mesmos valores da função "read_all()" (que usa calibração do módulo sensor).

### GY33_I2C.calibrate_white()

Realiza a calibração para o branco.  
O sensor deve estar posicionado sobre uma superfície branca adequada.

Após a calibração, a mesma superfície deverá retornar 255 em todos os valores RGBC ao executar um "read_cal()".

### GY33_I2C.calibrate_black()

Realiza a calibração para o preto.  
O sensor deve estar posicionado sobre uma superfície preta adequada.

Após a calibração, a mesma superfície deverá retornar 0 em todos os valores RGBC ao executar um "read_cal()".

### GY33_I2C.set_led(pwr=0)

Define a potência do LED (de 0 a 10).  
0 desliga o LED, 10 liga no máximo de potência.

### GY33_I2C.calibrate_white_balance()

Realiza uma calibração de balanço de branco.  
O sensor deve estar posicionado sobre uma superfície branca adequada.

Esse procedimento é feito pelo microcontrolador embutido e afeta os últimos 4 valores (Red, Green, Blue, Color) retornados por "read_all()".  
O microcontrolador não realiza calibração para preto.

## Exemplos

```python
import machine
import gy33_i2c
import time

i2c = machine.I2C(0, freq=100000)
gy33 = gy33_i2c.GY33_I2C(i2c, addr=90)

gy33.set_led(10)  # Potência máxima

while True:
    print(gy33.read_calibrated())
    time.sleep(1)
```
