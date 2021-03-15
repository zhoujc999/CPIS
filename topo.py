from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        cc_ctl = self.addHost( 'cc_ctl', ip='10.0.0.1/24')
        eng_ctl = self.addHost( 'eng_ctl', ip='10.0.0.2/24')
        simulator = self.addHost( 'sim' )
        m_eng_ctl = self.addHost( 'm_eng_ctl', ip='100.0.0.2/8')
        m_cc_ctl = self.addHost( 'm_cc_ctl', ip='100.0.0.3/8')
        cpis_main = self.addHost( 'cpis_main', ip='100.0.0.1/8')
        s1 = self.addSwitch("s1")

        # Add links
        self.addLink( cc_ctl, eng_ctl)
        self.addLink( cpis_main, s1)
        self.addLink( m_cc_ctl, s1)
        self.addLink( m_eng_ctl, s1)
	# self.addLink( leftHost, rightHost, params1={'ip' : '100.0.0.1/24' }, params2={'ip' : '100.0.0.3/24' })

topos = { 'mytopo': ( lambda: MyTopo() ) }
