import sounddevice as sd

print("--- PROCURANDO DISPOSITIVOS (DRIVER MME) ---")

# Vamos listar apenas os dispositivos MME (que são os mais compatíveis)
# O hostapi=0 geralmente é o MME no Windows
for i, device in enumerate(sd.query_devices()):
    if device['hostapi'] == 0: # Filtra só MME
        nome = device['name']
        inputs = device['max_input_channels']
        outputs = device['max_output_channels']
        
        # Marcador visual para facilitar
        tipo = ""
        if "CABLE Input" in nome: tipo = " <--- USE ESTE PARA 'SAÍDA VIRTUAL'"
        if "CABLE Output" in nome: tipo = " <--- (NÃO USE ESTE)"
        if "Realtek" in nome and inputs > 0: tipo = " <--- PROVÁVEL MICROFONE REAL"
        if "SF-VOICE" in nome and inputs > 0: tipo = " <--- SEU MICROFONE SF"
        if "SF-VOICE" in nome and outputs > 0: tipo = " <--- SEU FONE DE RETORNO"

        print(f"ID {i}: {nome} (In: {inputs}, Out: {outputs}){tipo}")

print("\n------------------------------------------------")
print("Anote os números (IDs) que apareceram marcados acima e coloque no script principal.")