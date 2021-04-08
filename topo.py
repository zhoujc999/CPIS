from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        cc_ctl = self.addHost( 'cc_ctl', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        eng_ctl = self.addHost( 'eng_ctl', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        simulator = self.addHost( 'sim' )
        m_eng_ctl = self.addHost( 'm_eng_ctl', ip='100.0.0.2/8')
        m_cc_ctl = self.addHost( 'm_cc_ctl', ip='100.0.0.3/8')
        cpis_main = self.addHost( 'cpis_main', ip='100.0.0.1/8')
        s2 = self.addSwitch("s2")
        s1 = self.addSwitch("s1")
        attacker = self.addHost( 'attacker', ip='10.0.0.9/24', mac='00:00:00:00:00:09')

        # Add links
        self.addLink( cc_ctl, s1)
        self.addLink( eng_ctl, s1)
        self.addLink( attacker, s1)
        self.addLink( cpis_main, s2)
        self.addLink( m_cc_ctl, s2)
        self.addLink( m_eng_ctl, s2)
	# self.addLink( leftHost, rightHost, params1={'ip' : '100.0.0.1/24' }, params2={'ip' : '100.0.0.3/24' })

topos = { 'mytopo': ( lambda: MyTopo() ) }
