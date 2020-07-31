import json, sys, os

limitfolder = sys.argv[1]
removeHutb4j4 = False
if len(sys.argv) > 2:
  removeHutb4j4 = not (sys.argv[2] == "False")

print removeHutb4j4
#Hct_cross_sec = 48.4
#Hut_cross_sec = 60.34

Hct_cross_sec = 1
Hut_cross_sec = 1

Hut_limits = json.loads(open(os.path.join(limitfolder, 'Hut_limits.json')).read())
for key in Hut_limits:
    for number_type in Hut_limits[key]:
        if isinstance(Hut_limits[key][number_type], list):
            Hut_limits[key][number_type][0] = round(Hut_limits[key][number_type][0]*Hut_cross_sec, 2)
            Hut_limits[key][number_type][1] = round(Hut_limits[key][number_type][1]*Hut_cross_sec, 2)
        else:
            Hut_limits[key][number_type] = round(Hut_limits[key][number_type]*Hut_cross_sec, 2)
        if number_type == 'observed':
            Hut_limits[key][number_type] = 'X'#*Hut_cross_sec

if removeHutb4j4:
  Hut_table = """
    \\begin{{tabular}}{{|l|c|c|c|c|c|c|}}
      \hline
      Category & $\sigma_{{exp}} - 2\sigma$ & $\sigma_{{exp}} - 1\sigma$ & $\sigma_{{exp}}$ & $\sigma_{{obs}}$ & $\sigma_{{exp}} + 1\sigma$ & $\sigma_{{exp}} + 2\sigma$ \\\\ \hline
      $b2j3$ & {j3b2M2sig} & {j3b2M1sig} & {j3b2Exp} & {j3b2Obs} & {j3b2P1sig} & {j3b2P2sig} \\\\
      $b2j4$ & {j4b2M2sig} & {j4b2M1sig} & {j4b2Exp} & {j4b2Obs} & {j4b2P1sig} & {j4b2P2sig} \\\\
      $b3j3$ & {j3b3M2sig} & {j3b3M1sig} & {j3b3Exp} & {j3b3Obs} & {j3b3P1sig} & {j3b3P2sig} \\\\
      $b3j4$ & {j4b3M2sig} & {j4b3M1sig} & {j4b3Exp} & {j4b3Obs} & {j4b3P1sig} & {j4b3P2sig} \\\\
      all & {allM2sig} & {allM1sig} & {allExp} & {allObs} & {allP1sig} & {allP2sig} \\\\ \hline
   \end{{tabular}}
""".format(
        j3b2M2sig=Hut_limits['b2j3']['two_sigma'][0], j3b2M1sig=Hut_limits['b2j3']['one_sigma'][0], j3b2Exp=Hut_limits['b2j3']['expected'], j3b2Obs=Hut_limits['b2j3']['observed'], j3b2P1sig=Hut_limits['b2j3']['one_sigma'][1], j3b2P2sig=Hut_limits['b2j3']['two_sigma'][1], 
        j4b2M2sig=Hut_limits['b2j4']['two_sigma'][0], j4b2M1sig=Hut_limits['b2j4']['one_sigma'][0], j4b2Exp=Hut_limits['b2j4']['expected'], j4b2Obs=Hut_limits['b2j4']['observed'], j4b2P1sig=Hut_limits['b2j4']['one_sigma'][1], j4b2P2sig=Hut_limits['b2j4']['two_sigma'][1], 
        j3b3M2sig=Hut_limits['b3j3']['two_sigma'][0], j3b3M1sig=Hut_limits['b3j3']['one_sigma'][0], j3b3Exp=Hut_limits['b3j3']['expected'], j3b3Obs=Hut_limits['b3j3']['observed'], j3b3P1sig=Hut_limits['b3j3']['one_sigma'][1], j3b3P2sig=Hut_limits['b3j3']['two_sigma'][1], 
        j4b3M2sig=Hut_limits['b3j4']['two_sigma'][0], j4b3M1sig=Hut_limits['b3j4']['one_sigma'][0], j4b3Exp=Hut_limits['b3j4']['expected'], j4b3Obs=Hut_limits['b3j4']['observed'], j4b3P1sig=Hut_limits['b3j4']['one_sigma'][1], j4b3P2sig=Hut_limits['b3j4']['two_sigma'][1],
        #j4b4M2sig=Hut_limits['b4j4']['two_sigma'][0], j4b4M1sig=Hut_limits['b4j4']['one_sigma'][0], j4b4Exp=Hut_limits['b4j4']['expected'], j4b4Obs=Hut_limits['b4j4']['observed'], j4b4P1sig=Hut_limits['b4j4']['one_sigma'][1], j4b4P2sig=Hut_limits['b4j4']['two_sigma'][1],
        allM2sig=Hut_limits['all']['two_sigma'][0], allM1sig=Hut_limits['all']['one_sigma'][0], allExp=Hut_limits['all']['expected'], allObs=Hut_limits['all']['observed'], allP1sig=Hut_limits['all']['one_sigma'][1], allP2sig=Hut_limits['all']['two_sigma'][1], 
    )
else:
  Hut_table = """
    \\begin{{tabular}}{{|l|c|c|c|c|c|c|}}
      \hline
      Category & $\sigma_{{exp}} - 2\sigma$ & $\sigma_{{exp}} - 1\sigma$ & $\sigma_{{exp}}$ & $\sigma_{{obs}}$ & $\sigma_{{exp}} + 1\sigma$ & $\sigma_{{exp}} + 2\sigma$ \\\\ \hline
      $b2j3$ & {j3b2M2sig} & {j3b2M1sig} & {j3b2Exp} & {j3b2Obs} & {j3b2P1sig} & {j3b2P2sig} \\\\
      $b2j4$ & {j4b2M2sig} & {j4b2M1sig} & {j4b2Exp} & {j4b2Obs} & {j4b2P1sig} & {j4b2P2sig} \\\\
      $b3j3$ & {j3b3M2sig} & {j3b3M1sig} & {j3b3Exp} & {j3b3Obs} & {j3b3P1sig} & {j3b3P2sig} \\\\
      $b3j4$ & {j4b3M2sig} & {j4b3M1sig} & {j4b3Exp} & {j4b3Obs} & {j4b3P1sig} & {j4b3P2sig} \\\\
      $b4j4$ & {j4b4M2sig} & {j4b4M1sig} & {j4b4Exp} & {j4b4Obs} & {j4b4P1sig} & {j4b4P2sig} \\\\ \hline
      all & {allM2sig} & {allM1sig} & {allExp} & {allObs} & {allP1sig} & {allP2sig} \\\\ \hline
   \end{{tabular}}
""".format(
        j3b2M2sig=Hut_limits['b2j3']['two_sigma'][0], j3b2M1sig=Hut_limits['b2j3']['one_sigma'][0], j3b2Exp=Hut_limits['b2j3']['expected'], j3b2Obs=Hut_limits['b2j3']['observed'], j3b2P1sig=Hut_limits['b2j3']['one_sigma'][1], j3b2P2sig=Hut_limits['b2j3']['two_sigma'][1],
        j4b2M2sig=Hut_limits['b2j4']['two_sigma'][0], j4b2M1sig=Hut_limits['b2j4']['one_sigma'][0], j4b2Exp=Hut_limits['b2j4']['expected'], j4b2Obs=Hut_limits['b2j4']['observed'], j4b2P1sig=Hut_limits['b2j4']['one_sigma'][1], j4b2P2sig=Hut_limits['b2j4']['two_sigma'][1],
        j3b3M2sig=Hut_limits['b3j3']['two_sigma'][0], j3b3M1sig=Hut_limits['b3j3']['one_sigma'][0], j3b3Exp=Hut_limits['b3j3']['expected'], j3b3Obs=Hut_limits['b3j3']['observed'], j3b3P1sig=Hut_limits['b3j3']['one_sigma'][1], j3b3P2sig=Hut_limits['b3j3']['two_sigma'][1],
        j4b3M2sig=Hut_limits['b3j4']['two_sigma'][0], j4b3M1sig=Hut_limits['b3j4']['one_sigma'][0], j4b3Exp=Hut_limits['b3j4']['expected'], j4b3Obs=Hut_limits['b3j4']['observed'], j4b3P1sig=Hut_limits['b3j4']['one_sigma'][1], j4b3P2sig=Hut_limits['b3j4']['two_sigma'][1],
        j4b4M2sig=Hut_limits['b4j4']['two_sigma'][0], j4b4M1sig=Hut_limits['b4j4']['one_sigma'][0], j4b4Exp=Hut_limits['b4j4']['expected'], j4b4Obs=Hut_limits['b4j4']['observed'], j4b4P1sig=Hut_limits['b4j4']['one_sigma'][1], j4b4P2sig=Hut_limits['b4j4']['two_sigma'][1],
        allM2sig=Hut_limits['all']['two_sigma'][0], allM1sig=Hut_limits['all']['one_sigma'][0], allExp=Hut_limits['all']['expected'], allObs=Hut_limits['all']['observed'], allP1sig=Hut_limits['all']['one_sigma'][1], allP2sig=Hut_limits['all']['two_sigma'][1],
    )
Hut_table_filename = os.path.join(limitfolder, "Hut_limits_table.tex")
with open(Hut_table_filename, 'w') as table_file:
    table_file.write(Hut_table)
print "Hut:"
print Hut_table

Hct_limits = json.loads(open(os.path.join(limitfolder, 'Hct_limits.json')).read())
for key in Hct_limits:
    for number_type in Hct_limits[key]:
        if isinstance(Hct_limits[key][number_type], list):
            Hct_limits[key][number_type][0] = round(Hct_limits[key][number_type][0]*Hct_cross_sec, 2)
            Hct_limits[key][number_type][1] = round(Hct_limits[key][number_type][1]*Hct_cross_sec, 2)
        else:
            Hct_limits[key][number_type] = round(Hct_limits[key][number_type]*Hct_cross_sec, 2)
        if number_type == 'observed':
            Hct_limits[key][number_type] = 'X'#*Hct_cross_sec

Hct_table = """
    \\begin{{tabular}}{{|l|c|c|c|c|c|c|}}
      \hline
      Category & $\sigma_{{exp}} - 2\sigma$ & $\sigma_{{exp}} - 1\sigma$ & $\sigma_{{exp}}$ & $\sigma_{{obs}}$ & $\sigma_{{exp}} + 1\sigma$ & $\sigma_{{exp}} + 2\sigma$ \\\\ \hline
      $b2j3$ & {j3b2M2sig} & {j3b2M1sig} & {j3b2Exp} & {j3b2Obs} & {j3b2P1sig} & {j3b2P2sig} \\\\
      $b2j4$ & {j4b2M2sig} & {j4b2M1sig} & {j4b2Exp} & {j4b2Obs} & {j4b2P1sig} & {j4b2P2sig} \\\\
      $b3j3$ & {j3b3M2sig} & {j3b3M1sig} & {j3b3Exp} & {j3b3Obs} & {j3b3P1sig} & {j3b3P2sig} \\\\
      $b3j4$ & {j4b3M2sig} & {j4b3M1sig} & {j4b3Exp} & {j4b3Obs} & {j4b3P1sig} & {j4b3P2sig} \\\\
      $b4j4$ & {j4b4M2sig} & {j4b4M1sig} & {j4b4Exp} & {j4b4Obs} & {j4b4P1sig} & {j4b4P2sig} \\\\ \hline
      all & {allM2sig} & {allM1sig} & {allExp} & {allObs} & {allP1sig} & {allP2sig} \\\\ \hline
   \end{{tabular}}
""".format(
        j3b2M2sig=Hct_limits['b2j3']['two_sigma'][0], j3b2M1sig=Hct_limits['b2j3']['one_sigma'][0], j3b2Exp=Hct_limits['b2j3']['expected'], j3b2Obs=Hct_limits['b2j3']['observed'], j3b2P1sig=Hct_limits['b2j3']['one_sigma'][1], j3b2P2sig=Hct_limits['b2j3']['two_sigma'][1], 
        j4b2M2sig=Hct_limits['b2j4']['two_sigma'][0], j4b2M1sig=Hct_limits['b2j4']['one_sigma'][0], j4b2Exp=Hct_limits['b2j4']['expected'], j4b2Obs=Hct_limits['b2j4']['observed'], j4b2P1sig=Hct_limits['b2j4']['one_sigma'][1], j4b2P2sig=Hct_limits['b2j4']['two_sigma'][1], 
        j3b3M2sig=Hct_limits['b3j3']['two_sigma'][0], j3b3M1sig=Hct_limits['b3j3']['one_sigma'][0], j3b3Exp=Hct_limits['b3j3']['expected'], j3b3Obs=Hct_limits['b3j3']['observed'], j3b3P1sig=Hct_limits['b3j3']['one_sigma'][1], j3b3P2sig=Hct_limits['b3j3']['two_sigma'][1], 
        j4b3M2sig=Hct_limits['b3j4']['two_sigma'][0], j4b3M1sig=Hct_limits['b3j4']['one_sigma'][0], j4b3Exp=Hct_limits['b3j4']['expected'], j4b3Obs=Hct_limits['b3j4']['observed'], j4b3P1sig=Hct_limits['b3j4']['one_sigma'][1], j4b3P2sig=Hct_limits['b3j4']['two_sigma'][1], 
        j4b4M2sig=Hct_limits['b4j4']['two_sigma'][0], j4b4M1sig=Hct_limits['b4j4']['one_sigma'][0], j4b4Exp=Hct_limits['b4j4']['expected'], j4b4Obs=Hct_limits['b4j4']['observed'], j4b4P1sig=Hct_limits['b4j4']['one_sigma'][1], j4b4P2sig=Hct_limits['b4j4']['two_sigma'][1],
        allM2sig=Hct_limits['all']['two_sigma'][0], allM1sig=Hct_limits['all']['one_sigma'][0], allExp=Hct_limits['all']['expected'], allObs=Hct_limits['all']['observed'], allP1sig=Hct_limits['all']['one_sigma'][1], allP2sig=Hct_limits['all']['two_sigma'][1], 
    )
Hct_table_filename = os.path.join(limitfolder, "Hct_limits_table.tex")
with open(Hct_table_filename, 'w') as table_file:
    table_file.write(Hct_table)

print 'Hct:'
print Hct_table
