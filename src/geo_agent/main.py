from crewai import Crew, Process
from .tasks import task_geocode, task_buffer, task_filter, task_render_map, geo_agent


def main():
    user_query = "I want to see all the mining concessions around SANTA province in Peru, Make a buffer of 40kms using city center of SANTA as reference point"
    mining_crew = Crew(
        agents=[geo_agent],
        tasks=[task_geocode, task_buffer, task_filter, task_render_map],
        process=Process.sequential,
        verbose=True
    )

    mining_crew.kickoff(inputs = {"query": user_query})

if __name__ == "__main__":
    main()
