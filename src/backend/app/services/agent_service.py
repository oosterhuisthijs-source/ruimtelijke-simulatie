"""
Agentic orchestrator using Ollama tool use.
Streams reasoning steps, tool calls, and final response as SSE events.
"""
import json
from typing import AsyncGenerator

from ollama import AsyncClient

from app.config import settings
from app.services.agent_tools import TOOLS, execute_tool

ORCHESTRATOR_MODEL = "qwen2.5:14b"

# Compact column schema for the agent — grouped by theme
COLUMN_SCHEMA = """
EXACTE KOLOMNAMEN (gebruik deze letterlijk in SQL, tabel = 'df'):

Filter/groepeer kolommen: h3_id, year_int (2018-2023), gemeentenaam, wijknaam, buurtnaam

Demografie: aantal_inwoners_sum, aantal_mannen_sum, aantal_vrouwen_sum,
  aantal_inwoners_0_tot_15_jaar_sum, aantal_inwoners_15_tot_25_jaar_sum,
  aantal_inwoners_25_tot_45_jaar_sum, aantal_inwoners_45_tot_65_jaar_sum,
  aantal_inwoners_65_jaar_en_ouder_sum, aantal_geboorten_sum,
  aantal_eenpersoonshuishoudens_sum, aantal_eenouderhuishoudens_sum,
  aantal_tweeouderhuishoudens_sum, aantal_part_huishoudens_sum

Wonen: aantal_woningen_sum, aantal_huurwoningen_in_bezit_woningcorporaties_sum,
  aantal_niet_bewoonde_woningen_sum, aantal_meergezins_woningen_sum,
  gemiddelde_woz_waarde_woning_area_weighted_average,
  gemiddelde_huishoudensgrootte_area_weighted_average,
  percentage_huurwoningen_area_weighted_average,
  percentage_koopwoningen_area_weighted_average,
  aantal_woningen_bouwjaar_voor_1945_sum, aantal_woningen_bouwjaar_45_tot_65_sum,
  aantal_woningen_bouwjaar_65_tot_75_sum, aantal_woningen_bouwjaar_75_tot_85_sum,
  aantal_woningen_bouwjaar_85_tot_95_sum, aantal_woningen_bouwjaar_95_tot_05_sum,
  aantal_woningen_bouwjaar_05_tot_15_sum, aantal_woningen_bouwjaar_15_en_later_sum

Sociaal-economisch: aantal_personen_met_uitkering_onder_aowlft_sum,
  percentage_geb_nederland_herkomst_nederland_area_weighted_average,
  percentage_geb_nederland_herkomst_buiten_europa_area_weighted_average,
  percentage_geb_buiten_nederland_herkmst_buiten_europa_area_weighted_average

Gebouwfuncties: num_woonfunctie, num_kantoorfunctie, num_industriefunctie,
  num_winkelfunctie, num_onderwijsfunctie, num_gezondheidszorgfunctie,
  num_sportfunctie, num_logiesfunctie, num_bijeenkomstfunctie, num_overige_gebruiksfunctie

Landgebruik bebouwing: bebouwing_in_primair_bebouwd_gebied_fraction,
  bebouwing_in_secundair_bebouwd_gebied_fraction, bebouwing_in_buitengebied_fraction,
  hoofdinfrastructuur_en_spoorbaanlichamen_fraction, zonneparken_fraction

Landgebruik natuur: loofbos_fraction, naaldbos_fraction, heide_fraction,
  agrarisch_gras_fraction, gras_in_primair_bebouwd_gebied_fraction,
  duinen_met_hoge_vegetatie_fraction, duinen_met_lage_vegetatie_fraction,
  zoet_water_fraction, zout_water_fraction, rietvegetatie_fraction

Landgebruik landbouw: granen_fraction, maïs_fraction, aardappelen_fraction,
  bieten_fraction, glastuinbouw_fraction, bloembollen_fraction

Milieu/klimaat: geluid_lden, hitte, lichtemissie, groundheight,
  flooddepth_1, flooddepth_2, flooddepth_3, flooddepth_4, flooddepth_5

BELANGRIJK: Gebruik ALTIJD year_int voor jaarselectie. NOOIT 'year', 'year_label' of 'year_ms'.
"""

SYSTEM_PROMPT = f"""Je bent een ruimtelijke data-analist voor Nederland met toegang tot een H3 hexagon dataset (225.684 gebieden, resolutie ~250m, jaren 2018-2023).

{COLUMN_SCHEMA}

Werkwijze:
1. Analyseer de vraag en bepaal welke kolommen je nodig hebt (gebruik de schema boven)
2. Gebruik tools om data op te halen — meerdere aanroepen zijn prima
3. Als je relevante hexagonen vindt, gebruik highlight_hexagons om ze op de kaart te tonen
4. Geef een concreet, beleidsrelevant antwoord in het Nederlands

Wees specifiek: noem gemeenten, cijfers, en gebruik altijd exacte kolomnamen uit het schema."""


async def run_agent(
    question: str,
    df,
    som,
    history: list[dict],
    max_steps: int = 6,
) -> AsyncGenerator[str, None]:
    """
    Run the agentic loop and yield SSE-formatted events.
    Events: thinking | tool_call | tool_result | response | error | done
    """
    client = AsyncClient()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Include conversation history
    for msg in history[-6:]:  # keep last 3 exchanges
        messages.append(msg)
    messages.append({"role": "user", "content": question})

    def sse(event_type: str, **kwargs) -> str:
        return f"data: {json.dumps({'type': event_type, **kwargs})}\n\n"

    try:
        for step in range(max_steps):
            response = await client.chat(
                model=ORCHESTRATOR_MODEL,
                messages=messages,
                tools=TOOLS,
            )

            msg = response.message

            # Stream any thinking text
            if msg.content:
                yield sse("thinking", content=msg.content)

            # No tool calls → final answer
            if not msg.tool_calls:
                yield sse("response", content=msg.content)
                yield sse("done")
                return

            # Append assistant message with tool calls
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                {"function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]})

            # Execute each tool call
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments

                yield sse("tool_call", name=name, args=args)

                result = execute_tool(name, args, df, som)

                # Handle highlight sentinel — emit map event before tool_result
                if result.startswith("__HIGHLIGHT__:"):
                    payload = json.loads(result[14:])
                    yield sse("highlight", h3_ids=payload["h3_ids"], label=payload["label"])
                    result = f"Kaart bijgewerkt: {len(payload['h3_ids'])} hexagonen gemarkeerd als '{payload['label']}'."

                # Truncate very long results for context window
                if len(result) > 2000:
                    result = result[:2000] + "\n...(afgekapt)"

                yield sse("tool_result", name=name, content=result)

                messages.append({
                    "role": "tool",
                    "content": result,
                })

        # Exceeded max steps — ask for final answer without tools
        response = await client.chat(
            model=ORCHESTRATOR_MODEL,
            messages=messages + [{"role": "user", "content": "Geef nu je conclusie op basis van de opgehaalde data."}],
        )
        yield sse("response", content=response.message.content)
        yield sse("done")

    except Exception as e:
        yield sse("error", content=str(e))
        yield sse("done")
