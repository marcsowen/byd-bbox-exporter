#!/usr/bin/python3 -u

import socket
import time

from prometheus_client import start_http_server, Gauge

autarky = Gauge('autarky', "Autoarky of region", ['region_code'])
energy_mix = Gauge('energy_mix', 'Energy mix of region', ['region_code'])
num_installations = Gauge('num_installations', 'Number of installations', ['region_code', 'type', 'name'])
usage = Gauge('usage', 'Current amount per time period in kWh', ['region_code', 'type', 'name'])
installed_capacity = Gauge('installed_capacity', 'Total installed capacity', ['region_code', 'type', 'name'])

BUFFER_SIZE = 4096
byd_ok = 1
byd_error = 0
MESSAGE_0 = "010300000066c5e0"


def send_msg(client, msg, tout):
    client.send(bytes.fromhex(msg))
    client.settimeout(tout)
    try:
        data = client.recv(BUFFER_SIZE)
    except:
        return byd_error, 0
    d = []
    for n in range(len(data) - 2):
        d.append(data[n])
    crc = modbus_crc(d)
    crcx = data[len(data) - 1] * 0x100 + data[len(data) - 2]
    if crc != crcx:
        print("send_msg recv crc not ok (" + f"{crc:04x}" + "/" + f"{crcx:04x}" + ")")
        return byd_error, 0
    #        self.log_debug("send_msg crc=" + f"{crc:04x}" + " / " + f"{crcx:04x}" + " len=" + str(len(data)))
    return byd_ok, data


def modbus_crc(msg: str) -> int:
    crc = 0xFFFF
    for n in range(len(msg)):
        crc ^= msg[n]
        for i in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


if __name__ == '__main__':
    print("BYD BatteryBox exporter v0.1\n")
    ip = "192.168.178.121"
    port = 8080
    server_port = 3425

    print("BBox IP: " + str(ip) + "\n")
    print("Port        : " + str(server_port) + "\n")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))

    start_http_server(server_port)
    while True:
        res, data = send_msg(client, MESSAGE_0, 1.0)
        byd_serial = ""
        for x in range(3, 22):
            byd_serial = byd_serial + chr(data[x])
        byd_bmu_a = "V" + str(data[27]) + "." + str(data[28])
        byd_bmu_b = "V" + str(data[29]) + "." + str(data[30])
        byd_bms = "V" + str(data[31]) + "." + str(data[32])
        byd_bmu_type = chr(data[33] + 65)
        byd_bms_type = chr(data[34] + 65)
        byd_bms_qty = data[36] // 0x10
        byd_modules = data[36] % 0x10
        byd_batt_type_snr = data[5]

        if data[38] == 0:
            byd_application = "OffGrid"
        elif data[38] == 1:
            byd_application = "OnGrid"
        elif data[38] == 2:
            byd_application = "Backup"
        else:
            byd_application = "unknown"

        print("Serial      : " + byd_serial)
        print("BMU A       : " + byd_bmu_a)
        print("BMU B       : " + byd_bmu_b)
        print("BMU type    : " + str(byd_bmu_type))
        print("BMS         : " + byd_bms)
        print("BMS type    : " + str(byd_bms_type))
        print("Bat type    : " + str(byd_batt_type_snr))
        print("BMS QTY     : " + str(byd_bms_qty))
        print("Modules     : " + str(byd_modules))
        print("Application : " + byd_application)

        time.sleep(60)
