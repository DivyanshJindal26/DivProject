const { SlashCommandBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, ActionRowBuilder, CommandInteraction } = require('discord.js');
const { getDb } = require('../../helpers/mongodb')

module.exports = {
    data: new SlashCommandBuilder()
        .setName('user')
        .setDescription('Login, logout and all user related commands')
        .addSubcommand(subcommand =>
            subcommand
                .setName('login')
                .setDescription('Login to a user account.')
        )
        .addSubcommand(subcommand =>
            subcommand
                .setName('logout')
                .setDescription('Log out of a user account.')
        )
        .addSubcommand(subcommand =>
            subcommand
                .setName('create')
                .setDescription('Create a new user account')
        )
        .addSubcommand(subcommand =>
            subcommand
                .setName('forgot-password')
                .setDescription('Run forgot password for a specific user.')
        )
        .addSubcommand(subcommand =>
            subcommand
                .setName('verify-otp')
                .setDescription('Verify forget password OTP to reset password')
        ),
    
    
    async execute(interaction) {
        const subcommand = interaction.options.getSubcommand();

        if (subcommand == 'login') {
            const modal = new ModalBuilder()
                .setCustomId('userLogin')
                .setTitle('User Login')
            const usernameOption = new TextInputBuilder()
                .setCustomId('login-username')
                .setLabel('Username')
                .setStyle(TextInputStyle.Short)
                .setRequired(true)
            const passwordOption = new TextInputBuilder()
                .setCustomId('login-password')
                .setLabel('Password')
                .setStyle(TextInputStyle.Short)
                .setRequired(true)

            
            const firstActionRow = new ActionRowBuilder().addComponents(usernameOption);
            const secondActionRow = new ActionRowBuilder().addComponents(passwordOption);
            modal.addComponents(firstActionRow, secondActionRow);

            await interaction.showModal(modal);
        }

        if (subcommand == 'logout') {
            const userDB = getDb().collection('discord');
            const user1 = await userDB.findOne({
                userid:interaction.user.id
            });
            if (!user1) {
                await interaction.reply('You aren\'t logged into any user')
                return;
            }
            else {
                token = user1.tokens
                await fetch('http://127.0.0.1:5000/user/logout',{
                    method: 'POST',
                    headers: {
                        'X-API-KEY':'divyanshjindal',
                        'Content-Type': 'application/json',
                        'Authorization':token
                    },
                })
                    .then(response => {
                        if (!response.ok) {
                            interaction.reply('You aren\'t logged in');
                        }
                        else {
                            interaction.reply(`Successfully logged out!`)
                        }
                    })
                    .then(error => {
                    })
                    
                
            }
            
        }

        if (subcommand == 'create') {
            const modal = new ModalBuilder()
                .setCustomId('userCreate')
                .setTitle('User Creation')
            const usernameOption = new TextInputBuilder()
                .setCustomId('create-username')
                .setLabel('Username')
                .setStyle(TextInputStyle.Short)
                .setRequired(true)
            const passwordOption = new TextInputBuilder()
                .setCustomId('create-password')
                .setLabel('Password')
                .setStyle(TextInputStyle.Short)
                .setRequired(true)
            const emailOption = new TextInputBuilder()
                .setCustomId('create-email')
                .setLabel('EMail')
                .setStyle(TextInputStyle.Short)
                .setRequired(true)

            
            const firstActionRow = new ActionRowBuilder().addComponents(usernameOption);
            const secondActionRow = new ActionRowBuilder().addComponents(passwordOption);
            const thirdActionRow = new ActionRowBuilder().addComponents(emailOption);
            modal.addComponents(firstActionRow, secondActionRow, thirdActionRow);

            await interaction.showModal(modal);
        }
    }
}