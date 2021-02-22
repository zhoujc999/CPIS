from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        cc_ctl = self.addHost( 'cc_ctl' )
        eng_ctl = self.addHost( 'eng_ctl' )
        simulator = self.addHost( 'sim' )

        # Add links
        self.addLink( cc_ctl, eng_ctl, params1={'ip' : '10.0.0.1/24' }, params2={'ip' : '10.0.0.2/24' })
	# self.addLink( leftHost, rightHost, params1={'ip' : '100.0.0.1/24' }, params2={'ip' : '100.0.0.3/24' })

topos = { 'mytopo': ( lambda: MyTopo() ) }
