const { Client, GatewayIntentBits, ActivityType } = require('discord.js');
const { REST } = require('@discordjs/rest');
const { Routes } = require('discord-api-types/v9');


// importing variables from config file
const { BOT_TOKEN, PREFIX, MONGODB, CLIENT_ID } = require('./config');
const fs = require('fs');
const path = require('path');

// importing stuff from handlers n helpers
const { connectMongo, getDb } = require('./helpers/mongodb')
const commandHandler = require('./helpers/commandHelper');

// setting up client and bot status
const client = new Client({
    intents: [
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMessageReactions,
        GatewayIntentBits.GuildPresences,
        GatewayIntentBits.DirectMessages,
        GatewayIntentBits.DirectMessageReactions,
    ],
    presence: {
        status: "dnd",
        activities: [
            {
                name: "with DivBot ❤️",
                type: ActivityType.Playing
            }
        ]
    }
})

// registering modals
const modalHandlerFiles = fs.readdirSync('./commands/modal').filter(file => file.endsWith('.js'));
for (const file of modalHandlerFiles) {
    const modalHandler = require(`./commands/modal/${file}`);
    div = file.split('.')[0]
    commandHandler.registerModalHandler(div, modalHandler.execute);  // Register modal handler with its customId
}

// setting up slash commands from ./commands/slash
// Load slash commands
const slashCommandsPath = path.join(__dirname, 'commands/slash');
const slashCommandFiles = fs.readdirSync(slashCommandsPath).filter(file => file.endsWith('.js'));
for (const file of slashCommandFiles) {
    const command = require(path.join(slashCommandsPath, file));
    commandHandler.registerSlashCommand(command);
}

// Register slash commands with Discord
const commands = [];
for (const file of slashCommandFiles) {
    const command = require(path.join(slashCommandsPath, file));
    commands.push(command.data);
}

const rest = new REST().setToken(BOT_TOKEN);

(async () => {
    try {
        console.log('Started refreshing application (/) commands.');
         await rest.put(
            Routes.applicationCommands(CLIENT_ID),
            { body: commands },
        );
        console.log('Successfully reloaded application (/) commands.');
    } catch (error) {
        console.error(error);
    }
})();



// accepting interactions
client.on('interactionCreate', async interaction => {
    await commandHandler.handleInteraction(interaction);
    
});


// turning on the bot
client.once('ready', async () => {
    console.log(`Bot is turned on successfully!`);
    connectMongo();
})

client.login(BOT_TOKEN);