"""
Unipress Game Client
Client for communicating with the game server running in Docker container.
"""

import json
import time
from typing import Any, Dict, Optional

import requests


class UnipressClient:
    """Client for Unipress game server."""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        Initialize client.
        
        Args:
            server_url: URL of the game server (default: http://localhost:5000)
        """
        self.server_url = server_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        try:
            response = self.session.get(f"{self.server_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "unhealthy"}
    
    def list_games(self) -> Dict[str, Any]:
        """List available games."""
        try:
            response = self.session.get(f"{self.server_url}/games/list")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def run_game(self, game: str, difficulty: int = 5) -> Dict[str, Any]:
        """
        Run a specific game.
        
        Args:
            game: Game name or module (e.g., "jumper", "demo_jump")
            difficulty: Difficulty level 1-10 (default: 5)
        """
        try:
            # Map game names to modules
            game_modules = {
                "jumper": "unipress.games.jumper.game",
                "demo_jump": "unipress.games.demo_jump.game",
            }
            
            game_module = game_modules.get(game, game)
            
            data = {
                "game": game_module,
                "difficulty": difficulty
            }
            
            response = self.session.post(
                f"{self.server_url}/games/run",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def stop_game(self) -> Dict[str, Any]:
        """Stop currently running game."""
        try:
            response = self.session.post(f"{self.server_url}/games/stop")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def game_status(self) -> Dict[str, Any]:
        """Get current game status."""
        try:
            response = self.session.get(f"{self.server_url}/games/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def wait_for_game_completion(self) -> bool:
        """
        Wait for current game to complete (no timeout).

        Returns:
            True if game completed or error occurs
        """
        while True:
            status = self.game_status()
            
            if "error" in status:
                print(f"Error checking game status: {status['error']}")
                return False
            
            if not status.get("game_running", False):
                return True
            
            time.sleep(1)
        

def main():
    """Example usage of the client."""
    # Position mouse cursor at bottom-right corner with 2% offset toward center
    import tkinter as tk
    import subprocess
    
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    
    x = int(screen_width * 0.98)  # 2% from right edge
    y = int(screen_height * 0.98)  # 2% from bottom edge
    
    # print(f'Screen: {screen_width}x{screen_height}')
    # print(f'Moving mouse to: ({x}, {y})')
    #
    # subprocess.run(['xdotool', 'mousemove', str(x), str(y)])
    #
    client = UnipressClient()
    
    # Check server health
    health = client.health_check()
    print(f"Server health: {health}")
    
    if "error" in health:
        print("Server is not available. Make sure the Docker container is running.")
        return
    
    # List available games
    games = client.list_games()
    print(f"Available games: {json.dumps(games, indent=2)}")
    
    # Run jumper game with difficulty 7
    result = client.run_game("jumper", difficulty=5)
    print(f"Game start result: {result}")
    
    # Wait for game to complete
    print("Waiting for game to complete...")
    completed = client.wait_for_game_completion()
    
    if completed:
        print("Game completed!")


if __name__ == "__main__":
    main()
