import sys
# From 2016 paper, Hut limit on Xsec is ~ 1.23pb (utilisant le plot et une latte) on BR 0.34%
# From 2016 paper, Hct limit on Xsec is ~ 1.15pb (utilisant le plot et une latte) on BR 0.44%

out_of_the_box_limits_from_combine = {'Hut':0.3105, 'Hct':0.4355}
Xsec_2016 = {'Hut': 50.82, 'Hct': 38.88}
for coupling in out_of_the_box_limits_from_combine.keys():
    print coupling
    limit_from_combine = out_of_the_box_limits_from_combine[coupling]

    Xsec = Xsec_2016[coupling]
    realLimit = (limit_from_combine*Xsec)*float(0.1/1.36)
    print "Real limit: %f"%realLimit

    BR = realLimit*0.1904/(Xsec*1.32158)
    print "BR: %f %%"%(BR*100)

    if coupling == 'Hut':
        print "To be compared with 2016 paper, Hut limit on Xsec is ~ 1.23pb on BR 0.34%%"
    else:
        print "To be compared with 2016 paper, Hct limit on Xsec is ~ 1.15pb on BR 0.44%%"

##limit_from_combine = float(sys.argv[1])
#
##Xsec = 50.82 #Hut kirill
#Xsec = 38.88 #Hct kirill
#
##Xsec = 60.34 #Hut 2017ANv3
##Xsec = 48.4 #Hct 2017ANv3
#
##realLimit = (limit_from_combine*Xsec)*float(0.1/1.36)
#realLimit = (limit_from_combine*Xsec)*float(0.1)
#print "Real limit: %f"%realLimit
#
#BR = realLimit*0.1904/(Xsec*1.32158)
#print "BR: %f %%"%(BR*100)
#
#print "To be compared with 2016 paper, Hut limit on Xsec is ~ 1.23pb on BR 0.34%% \n\t Hct limit on Xsec is ~ 1.15pb on BR 0.44%%"
