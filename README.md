# CPIS
Immune system based security for cyber physical system

# Usage
To launch mininet, use
```
sudo mn --custom ./topo.py --topo mytopo -x
```

To launch individual hosts:

Host: sim `./vehicle_simulation.py`

Host: cpis_main `./cpis_main.py`

Host: m_cc_stl `./monitor_cc_ctl.py`

Host: m_eng_stl `./monitor_eng_ctl.py`

Host: eng_stl `python3 -u -m trace --ignore-dir=/usr --trace engine_ctrl.py  > pipe_eng_ctl`

Host: cc_stl `python3 -u -m trace --ignore-dir=/usr --trace cc_ctrl.py  > pipe_cc_ctl`

![20210315174044](https://user-images.githubusercontent.com/16992187/111244424-1ce64480-85c0-11eb-9f3f-35c483be6240.png)

![20210429140219](https://user-images.githubusercontent.com/16992187/116618236-a1ccb980-a8f3-11eb-881f-d90c573ffa5f.png)

