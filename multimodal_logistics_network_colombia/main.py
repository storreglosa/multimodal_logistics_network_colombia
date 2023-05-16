#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

def phubModel(argc, argv):
    # Setting out amplpy library
    # You can install amplpy with "python -m pip install amplpy"
    from amplpy import AMPL

    os.chdir(os.path.dirname(__file__) or os.curdir)
    model_directory = os.path.join(os.curdir, "data")

    # Creating the model
    ampl = AMPL()

    # Must be solved with a solver supporting the suffix dunbdd
    ampl.set_option("solver", "cplex")
    ampl.set_option("presolve", False)
    ampl.set_option("omit_zero_rows", False)
    
    # Load the AMPL model 
    ampl.eval(r"""
        # Setting groups 
        set Origin;#Conjunto de nodos generadores de carga
        set Destination;#Conjunto de nodos atractores de carga
        set CTL;#Conjunto de potenciales terminales de consolidación (hub)
        set PCTL;#Conjunto de potenciales terminales de distribución (hub)
        set Port;#Conjunto de puertos

        # Setting parameters
        param q;#Número de terminales abiertas
        
        param Fk{k in CTL};#Costo fijo de instalación de una terminal de consolidación en una terminal k ∈ K
        param Fm{m in PCTL};#Costo fijo de instalación de una terminal de distribución en una terminal m ∈ M

        param CAPk{k in CTL};#Capacidad de la terminal de consolidación k ∈ K
        param CAPm{m in PCTL};#Capacidad de la terminal de consolidación m ∈ M

        #param T_T{m in PCTL};#Costo de transporte unitario del origen i ∈ I al destino j ∈ J utilizando la alternativa de envío directo
        param Cijp{i in Origin, j in Destination, p in PCTL};##Costo de transporte unitario del origen i ∈ I al destino j ∈ J utilizando la alternativa de envío directo carretero al puerto p
        param Cijkp{i in Origin, j in Destination, k in CTL, p in Port};##Costo de transporte unitario del origen i ∈ I al destino j ∈ J utilizando la alternativade envío a través de la terminal k ∈ K al puerto p
        param Cijmp{i in Origin, j in Destination, m in PCTL, p in Port};##Costo de transporte unitario del origen i ∈ I al destino j ∈ J utilizando la alternativade envío a través de la terminal m ∈ M al puerto p    
        param Cijkmp{i in Origin, j in Destination,  k in CTL, m in PCTL, p in Port};#Costo de transporte unitario del origen i ∈ I al destino j ∈ J utilizando la alternativa de envío a través del par de terminales k ∈ K y m ∈ M al puerto p

        param Eijp{i in Origin, j in Destination, p in PCTL};##Costo de externalidad unitario del origen i ∈ I al destino j ∈ J utilizando la alternativa de envío directo carretero al puerto p
        param Eijkp{i in Origin, j in Destination, k in CTL, p in Port};##Costo de externalidad unitario del origen i ∈ I al destino j ∈ J utilizando la alternativade envío a través de la terminal k ∈ K al puerto p
        param Eijmp{i in Origin, j in Destination, m in PCTL, p in Port};##Costo de externalidad unitario del origen i ∈ I al destino j ∈ J utilizando la alternativade envío a través de la terminal m ∈ M al puerto p    
        param Eijkmp{i in Origin, j in Destination,  k in CTL, m in PCTL, p in Port};#Costo de externalidad unitario del origen i ∈ I al destino j ∈ J utilizando la alternativa de envío a través del par de terminales k ∈ K y m ∈ M al puerto p
        
        param Wij{i in Origin, j in Destination};#Demanda de carga a enviar del nodo de origen i ∈ I al destino j ∈ J

        
        # Setting variables
        var Yk{k in CTL} binary;  # = 1 if CTL built at k
        var Ym{m in PCTL} binary;  # = 1 if CTL built at m
        var Ykm{k in CTL, m in PCTL} binary;  # = 1 if Yk*Ym=1
        
        var Pijp{i in Origin, j in Destination, p in PCTL};#Proporción de flujo de mercancía que se envía directamente del origen i ∈ I al destino j ∈ J por el puerto p
        var Pijkp{i in Origin, j in Destination, k in CTL, p in Port};#Proporción de flujo que se envía del origen i ∈ I al destino j ∈ J a través de la terminal k ∈ K al puerto p
        var Pijmp{i in Origin, j in Destination, m in PCTL, p in Port};#Proporción de flujo que se envía del origen i ∈ I al destino j ∈ J a través de la terminal m ∈ M al puerto p
        var Pijkmp{i in Origin, j in Destination,  k in CTL, m in PCTL, p in Port};#Proporción de flujo que se envía del origen i ∈ I al destino j ∈ J a través de las terminales k ∈ K y m ∈ M al puerto p
        
        
        # Setting Objective Function
        
        minimize total_cost:
            sum {k in CTL} Yk[k]*Fk[k] + sum {m in PCTL} Ym[m]*Fm[m]
            + sum {i in Origin, j in Destination, p in PCTL} Pijp[i,j,p]*Wij[i,j]*(Cijp[i,j,p]+Eijp[i,j,p])
            + sum {i in Origin, j in Destination, k in PCTL, p in Port} Pijkp[i,j,k,p]*Wij[i,j]*(Cijkp[i,j,k,p]+Cijkp[i,j,k,p])
            + sum {i in Origin, j in Destination, m in CTL, p in Port} Pijmp[i,j,m,p]*Wij[i,j]*(Cijmp[i,j,m,p]+Cijmp[i,j,m,p])
            + sum {i in Origin, j in Destination, k in CTL, m in PCTL, p in Port} Pijkmp[i,j,k,m,p]*Wij[i,j]*(Cijkmp[i,j,k,m,p]+Eijkmp[i,j,k,m,p])

        ;

        # Restrictions
        subject to chosen_CTL:#que q terminales serán seleccionadas
            (sum{k in CTL} Yk[k]) + (sum{m in PCTL} Yk[m]) = q;
            
        subject to capacity {i in Origin, j in Destination}:#garantiza que el flujo de carga entre los nodos i y j es ruteado a través del envío directo o a través de las terminales que se encuentren disponibles
            (sum{p in Port} Pijp[i,j,p]) + (sum{k in CTL,p in Port} Pijkp[i,j,k,p]) + (sum{m in PCTL,p in Port} Pijkp[i,j,m,p]) 
            + (sum{k in CTL, m in PCTL, p in Port} Pijkmp[i,j,k,m,p]) = 1;
            
        subject to binary1 {k in CTL, m in PCTL}:#garantizan la resolución del problema de multiplicación de las variables binarias.
            Yk[k] + Ym[m] <= 1 + Ykm[k,m];
            
        subject to binary2 {k in CTL, m in PCTL}:#garantizan la resolución del problema de multiplicación de las variables binarias.
            2*Ykm[k,m] <= Yk[k] + Ym[m];
        
        subject to flow1 {k in CTL}:#garantizan que el flujo de carga que maneja cada terminal es menor o igual a la capacidad instalada
            (sum{i in Origin, j in Destination,p in Port} Pijkp[i,j,k,p]*Wij[i,j]) + (sum{i in Origin, j in Destination,  m in PCTL, p in Port} Pijkmp[i,j,k,m,p]*Wij[i,j])  <= CAPk[k]*Yk[k];
        subject to flow2 {m in PCTL}:#garantizan que el flujo de carga que maneja cada terminal es menor o igual a la capacidad instalada
            (sum{i in Origin, j in Destination,p in Port} Pijmp[i,j,m,p]*Wij[i,j]) + (sum{i in Origin, j in Destination,  k in CTL, p in Port} Pijkmp[i,j,k,m,p]*Wij[i,j])  <= CAPm[m]*Ym[m];
    
                
            """)
    # Read data
    ampl.read_data(os.path.join(model_directory, "phubmodel.dat"))