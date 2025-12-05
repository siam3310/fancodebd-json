{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-23.11"; # Or "unstable"
  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.nodejs_20 # For Node.js
    pkgs.python311 # For Python
  ];
  # Sets environment variables in the workspace
  env = {};
  # Search for the starship package in the nixpkgs channel and install it.
  # Help -> Show connection status for more details
  idx = {
    # Pre-warm the language servers for the following languages
    # The values in this list should be one of the following:
    # go, java, javascript, nix, python, rust, typescript
    preWarm = [
    ];
    workspace = {
      # Runs when a workspace is created
      onCreate = {
        npm-install = "npm install";
      };
      # Runs when a workspace is started
      onStart = {};
    };
  };
}
