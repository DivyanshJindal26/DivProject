const prefix = new Map();
const slash = new Map();
const modals = new Map();  // Map to store modal handlers
const { PREFIX } = require('../config');

module.exports = {

    registerPrefixCommand(command) {
        prefix.set(command.name, command);
    },

    registerSlashCommand(command) {
        slash.set(command.data.name, command);
    },

    registerModalHandler(customId, handler) {
        // Register modal handler for a specific modal customId
        modals.set(customId, handler);
    },

    async handleInteraction(interaction) {
        if (interaction.isCommand()) {
            // Handle slash commands
            const command = slash.get(interaction.commandName);
            if (!command) return;
            try {
                await command.execute(interaction);
            } catch (error) {
                console.error(error);
                await interaction.reply({ content: 'Error in this slash command.', ephemeral: true });
            }
        } else if (interaction.isModalSubmit()) {
            // Handle modal submissions
            const modalHandler = modals.get(interaction.customId);
            if (!modalHandler) return;
            try {
                await modalHandler(interaction);
            } catch (error) {
                console.error(error);
                await interaction.reply({ content: 'Error in this modal submission.', ephemeral: true });
            }
        }
    },

    async handleMessage(message) {
        if (!message.content.startsWith(PREFIX) || message.author.bot) return;
        const args = message.content.slice(PREFIX.length).trim().split(/ +/);
        const commandName = args.shift().toLowerCase();
        const command = prefix.get(commandName);
        if (!command) return;
        try {
            await command.execute(message, args);
        } catch (error) {
            console.error(error);
            message.reply('Error in prefix command');
        }
    },
};
