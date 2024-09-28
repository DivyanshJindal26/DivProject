const prefix = new Map();
const slash = new Map();
const { PREFIX } = require(`../config`)
module.exports = {

    registerPrefixCommand(command) {
        prefix.set(command.name, command);
    },

    registerSlashCommand(command) {
        slash.set(command.data.name, command);
    },

    async handleInteraction(interaction) {
        const command = slash.get(interaction.commandName);
        if (!command) return;
        try {
            await command.execute(interaction);
        } catch (error) {
            console.error(error);
            await interaction.reply({ content: 'Error in this slash command.', ephemeral: true });
        }
    },

    async handleMessage(message) {
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
